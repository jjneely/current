#! /usr/bin/python 

""" Channels store all the information for some collection of related rpms.

    Channels perform all the low-level DB/filesystem magic required 
    to organize, query, and otherwise deal with the RPM's themselves.
    
"""

import bsddb
import gzip
import os
import os.path
import pickle
import pprint
import rpm
import shelve
import stat
import string
import sys
import time
import copy
import xmlrpclib

import misc
from logger import *

# Prevents using an older database with incompatible code.
SCHEMA_VERSION = 6  # hunter 8/07/2002
                    # lalalala

class Channel:
    """Represents a single rpm collection.
    
    A channel is some logical collection of related RPMS. Might be a whole
    distribution (Red Hat Linux 7.1 i386) or just some add-on packages.
    (Duke Biology add-ons to RHL 7.1). A single channel can only serve
    one arch/os_release (although os_release might be dropped in the future).
    
    NOTE: This was originally called a repository in earlier versions
    of current.
    """
    
    def __init__(self):
        # we pickle off the channel, so I don't really want to use self...
        self.chanInfo = {}
        self.chanfile = None
        self.dep_files = None
        self.dep_provides = None
        self.dep_names = None
        self.dep_obsoletes = None
        self.rpm_index = None
        self.name_index = None
        self.src_index = None
        self.arch_index = None
        self.dep_srcrpms = None
        self.is_open = 0
        self._SEP = ':'

    
    def __del__(self):
        """ Equivalent to calling close explicitly."""

        if self.is_open:
            self.close()

    
    def check_consistency(self):
        all_ok = 1
        # This routine checks the following items:
        # 1. Does a filename exist for every RPM in the db?
        # 2. Same for SRPMS
        # 3. If configuration requires it, does an SRPM exist for every RPM?

        # Make sure the DB is open
        assert self.is_open

        # We've already checked the schema version and the db validity, in the
        # open() call.
        # First, check to make sure all RPMs in the name_index can get to a
        # file name, and then to an existing full path.
        # Any errors here are critical, so log 'em as such.
        for rpm in self.name_index.keys():
            if not self.name_index.has_key(rpm):
                log("ERROR: RPM %s doesn't appear to have a valid file name." % rpm, MANDATORY)
                all_ok = 0
            else:
                file = self.name_index[rpm]
                if not self.rpm_index.has_key(file):
                    log("ERROR: RPM %s has file name, but file name %s doesn't appear to map to path." % (rpm, file), MANDATORY)
                    all_ok = 0
                else:
                    path = self.rpm_index[file]
                    if not os.access(path, os.R_OK):
                        log('ERROR: RPM path %s not readable!' % path, MANDATORY)
                        all_ok = 0
            log ('RPM %s passed check.' % rpm, TRIVIA)

        # Done with the RPM checks.  If there were errors, jump out.
        if not all_ok:
            return

        # No errors so far, so check SRPMS
        for srpm in self.src_index.keys():
            path = self.src_index[srpm]
            if not os.access(path, os.R_OK):
                log ('ERROR SRPM path %s not readable!' % path, MANDATORY)
                all_ok = 0
            log ('SRPM %s passed check.' % srpm, TRIVIA)

        # Done with the SRPM checks.  If there were errors, jump out.
        if not all_ok:
            return

        # Check for RPM<->SRPM map, if it's set to warn or crit (1 or 2)
        check = int(self.chanInfo['srpm_check'])

        if check > 0:
            if check == 1:
                level = 'WARNING: '
            else:
                level = 'ERROR: '
            for rpm in self.name_index.keys():
                if not self.dep_srcrpms.has_key(rpm):
                    log (level+'RPM %s has no corresponding SRPM!' % rpm, MANDATORY)
                    all_ok = 0
                else:
                    log ('RPM %s has link to SRPM %s' % (rpm, self.dep_srcrpms[rpm]), TRIVIA)

        if not all_ok:
            return

        log ('All checks completed successfully.', DEBUG)
        

    def update(self):
        """ Update the database from rpms on the filesystem.

        This might be the creation of a new channel, or a true update of 
        an existing channel depending on the mode passed to open().

        """ 

        assert self.is_open
        assert self.open_mode in ('c', 'u')

        # Note that getPackage and getPackageSource dir is full of symlinks,
        # all the others contain real files. We use symlinks to allow people
        # to simply mirror ftp.redhat.com (or whatever) without eating up
        # even more disk than we do now.
        self.chanInfo['list_dir'] = '%s/%s' % \
            (self.chanInfo['web_dir'], 'listPackages')
        self.chanInfo['headers_dir'] = '%s/%s' % \
            (self.chanInfo['web_dir'], 'getPackageHeader')
        self.chanInfo['packagesource_dir'] = '%s/%s' % \
            (self.chanInfo['web_dir'], 'getPackageSource')
        self.chanInfo['package_dir'] = '%s/%s' % \
            (self.chanInfo['web_dir'], 'getPackage')
            
        # Make sure we have a directory for all the queries
        # The dirs might exist if this is a 2nd create...
        if not os.path.exists(self.chanInfo['list_dir']):
            os.makedirs(self.chanInfo['list_dir'])
        if not os.path.exists(self.chanInfo['headers_dir']):
            os.makedirs(self.chanInfo['headers_dir'])
        if not os.path.exists(self.chanInfo['packagesource_dir']):
            os.makedirs(self.chanInfo['packagesource_dir'])
        if not os.path.exists(self.chanInfo['package_dir']):
            os.makedirs(self.chanInfo['package_dir'])

        ## Actually add the data
        # add the sources first
        for dir in self.chanInfo['src_dirs']:
            self._addSrcDir(dir)
            
        # add binaries
        for dir in self.chanInfo['rpm_dirs']:
            self._addRpmDir(dir)

        # At this point, we need to make sure all rpm entries in the DB
        # actually have an RPM file, in case some were deleted.
        # FIXME - WORK ON THIS!
        # problem is, in order to remove an RPM, we have to have the package
        # available, which is kinda stupid...


    def _writeListPackagesCache(self):
        """ create a listPackages.lst cache file.

        listPackages information is static between db creates/updates. 
        Creating the cache this way significantly improves performance.
        """
        
        nlist = []
        for key in self.arch_index.keys():
            tmp = self.arch_index[key][:]

            # CLIENT BUG WORKAROUND
            # this rediculous step is because the client assumes the _first_
            # package will always work. Which it won't. (athlon on i686)
            # FIXME: Take this out in current 1.5
            tmp.sort(_orderArchs)

            for pkg in tmp:
                pkg.append(self.chanInfo['label'])
                nlist.append(pkg)
        nlist = (nlist,)

        filename = misc.PathJoin(self.chanInfo['list_dir'], 
                                 self.chanInfo['last_modified'])
        pl_file = gzip.GzipFile(filename, 'wb', 9)
        
        str = xmlrpclib.dumps(nlist, methodresponse=1)
        pl_file.write(str)
        pl_file.close()


    def close(self):
        """ Close the database(s) that make up this channel. """

        if not self.is_open:
            return    
        
        ## Close / write the pickle and cache file 
        if not self.open_mode == 'r':
            # Add the version/last_modified field
            self.chanInfo['last_modified'] = time.strftime("%Y%m%d%H%M%S",
                time.localtime(time.time()))

            # BUGFIX: Rewind the channel pickle, and THEN write the new copy.
            self.chanfile.seek(0)
            pickle.dump(self.chanInfo, self.chanfile)

            # Now write out the listPackages cache. 
            self._writeListPackagesCache()

        # Close all the actual files.
        self.chanfile.close()
        self.rpm_index.close()   
        self.name_index.close()
        self.src_index.close()  
        self.arch_index.close()  
        self.dep_files.close()   
        self.dep_provides.close()
        self.dep_names.close()
        self.dep_obsoletes.close()
        self.dep_srcrpms.close()
        self.is_open = 0        


    def getRpmFilename(self, pkg):
        """ Get the filename for a given pkg """

#        key_string = self._listToNVREArchString(pkg)
        if self.rpm_index.has_key(pkg):
            return self.rpm_index[pkg]
        else:
            return None  
        

    def getRpmFileByPkgName(self, pkg, arch):
        key = pkg + "-" +  arch
        if self.name_index.has_key(key):
            return self.name_index[key]
        else:
            log("Package %s and arch %s combination not found in name index"
                % (pkg, arch), TRIVIA)
            return None

        
    def addToNameIndex(self, pkg, arch, file):
        key = pkg + '-' + arch
        if self.name_index.has_key(key):
            if self.name_index[key] != file:
                log ("Replacing package %s, %s - why?" % (key, file), DEBUG2)
        self.name_index[key] = file


    def removeFromNameIndex(self, pkg, arch):
        key = pkg + '-' + arch
        if not self.name_index.has_key(key):
            log ("Trying to delete package %s which isn't in name index - why?"
                 % (key), DEBUG)
        else:
            del self.name_index[key]
                    

    def addToSourceLink(self, pkg, arch, name):
        key = pkg + '-' + arch
        if self.dep_srcrpms.has_key(key):
            if self.dep_srcrpms[key] != name:
                log ("Replacing source link for package %s - why?"
                     % (key), DEBUG)
        self.dep_srcrpms[key] = name


    def removeFromSourceLink(self, pkg, arch):
        key = pkg + '-' + arch
        if not self.dep_srcrpms.has_key(key):
            log ("Trying to delete package %s which isn't in srcrpms index - why?"
                 % (key), DEBUG)
        else:
            del self.dep_srcrpms[key]


    def getSrcRpmFilename(self, src_name):
        """ Given a RPMTAG_SOURCERPM string, locate the filename. """

        # This one is so easy it hurts (well, maybe not quite that easy...)
        if self.src_index.has_key(src_name):
            return self.src_index[src_name]
        else:
            return None
            

    def getPackageHeaderCache(self, header_name):
        """ Return an already unloaded package header """
        
        return "%s/%s" % (self.chanInfo['headers_dir'], header_name)


    def getPackageListCache(self):
        """ Return a pre-made list of all available packages. """

        return self.chanInfo['package_list']
        

    def getDependancy(self, dep):
        """ Get a list of NVREAS lists that solve a dependancy.

        We have three tables, dep_files, dep_names, and dep_provides that
        tell us which NVRE solves a particular dep. Get that NVRE, and 
        use that to find all the NVREAS's that match. (So that the 
        packagedb can pick the "best" for a particular client.

        We have the additional (unsolved) problem that we might have 
        multiple packages providing the same thing. Postfix and sendmail
        both provide a number of files. Some of the irc clients clash. 
        Right now we just grab the first solution to our problems and go.

        """

        if dep[0] == '/':
            # Treat it as a file dependency
            # FIXME: we should log duplicate entries in the database, but at
            # the moment we just grab the first solution. So if you have
            # both postfix and sendmail in the db, the first listed wins.
            
            if self.dep_files.has_key(dep):
                dep_file = self.dep_files[dep][0]   # <-- [0] FIXME

                # Here we return all possible archs for that pkg.
                return self.arch_index[dep_file]

            else:
                # No hit for that file. It can't be a provide or name,
                # (not if it starts with a /) so, we dump.
                return None
            
        else:
            # Try it first as a package name
            if self.dep_names.has_key(dep):
                # It _is_ a name dependancy
                dep_name = self.dep_names[dep][0] # <-- [0] FIXME

                # Here we return all possible archs for that pkg.
                return self.arch_index[dep_name]

            else:
                # else try it as a soname

                if self.dep_provides.has_key(dep):
                    tmp = self.dep_provides[dep][0] # <-- [0] FIXME

                    # In the provides table, its not a simple list of 
                    # NVRE strings like in dep_names or dep_files. We
                    # need to rip the NVRE string out of another list.
                    # NOTE: This is not the same problem as above that
                    #    has fix me's on it.
                    dep_name = tmp[0]    

                    # Here we return all possible archs for that pkg.   
                    return self.arch_index[dep_name]

                else:
                    # It was not found anywhere :(
                    return None


    def open(self, chan_info, mode='r'):
        """ Mostly this is opening the shelves that contain the big portions
        of the data...
        """

        #logfunc(locals())

        assert not self.is_open         
        assert mode in ('r', 'c', 'u')

        # channel open presents a mode of r, c and u. We must translate 
        # that into the modes of the needed component files.
        if mode == 'c':
            pickle_mode = 'w'
            shelve_mode = 'n'
        elif mode == 'r':
            pickle_mode = 'r'
            shelve_mode = 'r'
        else:
            pickle_mode = 'r+'
            shelve_mode = 'w'

        # To bring order and sanity to updating the pickle, we make 
        # the close function, and ONLY the close function, actually write
        # the pickle to disk.
        self.open_mode = mode

        # for clarity
        db_dir = chan_info['db_dir']

        # Go ahead and open the pickle file - well there's anything
        # there is about to be determined.
        chan_filename = '%s/%s' % (db_dir, 'current.chan')
        self.chanfile = open(chan_filename, pickle_mode)
 
        if mode == 'c':
            self.chanInfo = copy.deepcopy(chan_info)
    
            # We only set the schema version on create - updates only work
            # for the same schema version.
            self.chanInfo['schema_version'] = SCHEMA_VERSION
        else: # ('u', 'r')
            # We only read the pickle in when opening in read or
            # update mode - if we're writing, the chanInfo in memory struct
            # had better already be populated.
            self.chanInfo = pickle.load(self.chanfile)

            # people don't always re-create their DB's when the README
            # tells them to.
            if not self.chanInfo.has_key('schema_version') or \
                self.chanInfo['schema_version'] != SCHEMA_VERSION:
                log("ERROR: Wrong db schema version detected. " \
                    "Recreate your database.", MANDATORY)
                log("ERROR: Saw %s, expecting %s" % 
                    (self.chanInfo['schema_version'], SCHEMA_VERSION))
                raise Exception("ERROR: Wrong db schema version detected.")

        # Open the other files
        self.rpm_index = bsddb.btopen('%s/%s' % (db_dir,
                                      'rpm_index.wdb'), shelve_mode)
        self.name_index = bsddb.btopen('%s/%s' % (db_dir,
                                       'name_index.wdb'), shelve_mode)
        self.src_index = bsddb.btopen('%s/%s' % (db_dir, 
                                      'src_index.wdb'), shelve_mode)
        self.arch_index = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir, 
                                            'arch_index.wdb'), shelve_mode))

        # Dependancy information
        self.dep_files = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir, 
                                           'dep_files.wdb'), shelve_mode))
        self.dep_provides = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir, 
                                              'dep_provides.wdb'), shelve_mode))
        self.dep_names = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir, 
                                           'dep_names.wdb'), shelve_mode))
        self.dep_obsoletes = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir,
                                               'dep_obsoletes.wdb'), shelve_mode))
        self.dep_srcrpms = shelve.BsdDbShelf(bsddb.btopen('%s/%s' % (db_dir,
                                             'dep_srcrpms.wdb'), shelve_mode))
        self.is_open = 1

        
    def dump(self, flags='rsanpfivom'):
        """Mostly for debugging - just print each table/index out"""

        assert self.is_open 

        ## FIXME??? I left these prints - should they become log()'s?
        if 'i' in flags:   # i is the second letter of pickle
            print "CHANNEL PICKLE"
            print "====================================="
            pprint.pprint(self.chanInfo)
            # We also include some statistical data for 'i'
            print 'rpm count =', len(self.rpm_index)
            print 'srpm count =', len(self.src_index)
            print 'arch index count =', len(self.arch_index)
            print 'dep names =', len(self.dep_names)
            print 'dep provides =', len(self.dep_provides)
            print 'dep files =', len(self.dep_files)
            print
                
        if 'r' in flags:
            print "RPM_INDEX"
            print "====================================="
            for key in self.rpm_index.keys():
                print "  [", key, "] =", self.rpm_index[key]
            print
                
        if 's' in flags:
            print "SRC_INDEX"
            print "====================================="
            for key in self.src_index.keys():
                print "  [", key, "] =", self.src_index[key]
                
        if 'a' in flags:
            print "ARCH_INDEX"
            print "====================================="
            for key in self.arch_index.keys():
                value = self.arch_index[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value
                
        if 'n' in flags:
            print "DEP_NAMES_INDEX"
            print "====================================="
            for key in self.dep_names.keys():
                value = self.dep_names[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value
                
        if 'p' in flags:
            print "DEP_PROVIDES_INDEX"
            print "====================================="
            for key in self.dep_provides.keys():
                value = self.dep_provides[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value
                
        if 'f' in flags:
            print "DEP_FILES_INDEX"
            print "====================================="
            for key in self.dep_files.keys():
                value = self.dep_files[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value

        if 'o' in flags:
            print "DEP_OBSOLETES_INDEX"
            print "====================================="
            for key in self.dep_obsoletes.keys():
                value = self.dep_obsoletes[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value

        if 'm' in flags:
            print "NAME_INDEX"
            print "====================================="
            for key in self.name_index.keys():
                value = self.name_index[key]
                if len(value) > 1 or 'v' in flags:
                    print " ", key, "=", value


    def _getHeaderFromFilename(self, pathname, binary=1):
        """ Open a pathname as an rpm, and retrive the header from it. """

        try: 
            fd = os.open(pathname, os.O_RDONLY)
            (header, isSource) = rpm.headerFromPackage(fd)
            os.close(fd)

        except:
            logException()
            log("Warning: Could not open package %s" % pathname, MANDATORY)
            return (None, None)
        
        if header == None: 
            ## FIXME, we should have an error stream or callback or
            ## something - this is crude.
            log("Warning: Could not read package %s" % pathname, MANDATORY)
            return (None, None)

        # FIXME: possibly, we should do more than just log the infraction
        # These infractions will be handled in the calling routines, so just
        # log it at the debug level and go on with life.
        if isSource and binary:
            # FIXME: need something better here
            log("Warning: source rpm %s found in bin dir." % pathname, DEBUG)
            return (header, isSource)
        elif ((not isSource) and (not binary)):
            # Opposite of previous test - expecting source rpm, found binary
            log("Warning: binary rpm %s found in src dir." % pathname, DEBUG)
            return (header, isSource)
        else:
            return (header, isSource)
                
                
    def _addRpmDir(self, dirname):
        """ Add an entire directory of rpms all at once """
        
        if not os.path.isdir(dirname):
            log("Warning: %s was not a valid dir" % dirname, MANDATORY)
            return

        for file in os.listdir(dirname):
            pathname = misc.PathJoin(dirname, file)
            self._addRpmPackage(pathname)


    def _addRpmPackage(self, pathname):
        """ Add a single Rpm to the channel. 

        PLEASE NOTE that you must keep this method and _deleteRpmPackage in
        sync.

        """

        (hdr, isSource) = self._getHeaderFromFilename(pathname)

        if isSource or hdr == None:
            return
        
        file = os.path.basename(pathname)
        log("", DEBUG2)
        #self.dump('namv')
        log("-------------------------------------", DEBUG2)
        log("Examing %s" % file, DEBUG)
        #log("DB before add:", DEBUG)
        #self.dump('namvp')

        # BUGFIX: We were recording the rpm.RPMTAG_SIZE from the header,
        #   but RHN itself actually returns the stat() size of the rpm. 
        #   That makes sense, as what size is used for is a progress bar
        #   for downloads.
        rpm_size = str(os.stat(pathname)[stat.ST_SIZE])

        # Just generate these strings once
        nvre = self._hdrToNVREString(hdr)
        nvrea = self._hdrToNVREArchString(hdr)
        nvreas_list = self._hdrToNVREASList(hdr, rpm_size)

        # Added to make the package name to filename mapping easier
        pkg_name = nvreas_list[0]
        
        ### Database sanity checking ###

        # Check and make sure we don't have different versions for 
        # the same package.
        dups = []
        if self.dep_names.has_key(pkg_name):
            log("dep_names[%s] = %s" % (pkg_name, 
                                        self.dep_names[pkg_name]), DEBUG2)

            hits = self.dep_names[pkg_name]
            log("hits = %s" % hits, DEBUG2)

            for hit in hits:
                # self.arch_index[hit] is a list of lists.
                # we want to appeand ea item in this list to dups
                for item in self.arch_index[hit]:
                    dups.append(item)
                    log ("dups = %s" % dups, DEBUG2)

            log("dups = %s" % dups, DEBUG2)

            # Ok, we can have X different archs, as long as their 
            # VRE's all match
            for pkg in dups:

                # compare the archs first, if they're different, you're
                # done with this iteration.
                if nvreas_list[4] != pkg[4]:
                    continue

                # log("Same arch in compare - dumping DB:", DEBUG)
                # self.dump('namvp')
                # Compare the two VRE's and find out which is newer
                # BUG? We do this both ways to try and track down some
                # odd version problems people are seeing
#X                FIXME: labelCompare expects epoch = None, not ""
                compare = rpm.labelCompare( (nvreas_list[3], nvreas_list[1], nvreas_list[2]),
                                  (pkg[3], pkg[1], pkg[2]))
                # Log the order we're comparing for debugging...
                log("Comparing packages: %s-%s-%s and %s-%s-%s yields %s" %
                    (nvreas_list[0], nvreas_list[1], nvreas_list[2],
                     pkg[0], pkg[1], pkg[2], compare), DEBUG2)

                compare2 = rpm.labelCompare((pkg[3], pkg[1], pkg[2]), 
                                  (nvreas_list[3], nvreas_list[1], nvreas_list[2]))
                log("Comparing packages: %s-%s-%s and %s-%s-%s yields %s" %
                    (pkg[0], pkg[1], pkg[2], 
                     nvreas_list[0], nvreas_list[1], nvreas_list[2], 
                     compare2), DEBUG2)

                if ( compare < 0 ):
                    log("Package is older than package already in database.", DEBUG2)
                    return
                if ( compare == 0 ):
                    log ("Package is same as in database - probably a symlink...", DEBUG2)
                    return

                # must be ok to proceed...
                # package is newer, so we need to remove the older package
                # currently in the db.  
                filename = self.getRpmFileByPkgName(pkg[0], pkg[4])
                print "pkg0 = %s, pkg4 = %s, filename = %s" % \
                    (pkg[0], pkg[4], filename)

                # Now go find the path to it.
                fullname = self.getRpmFilename(filename)
                if fullname == None:
                    log("Error: Could not find filename of package to delete",
                        MANDATORY)
                    continue
                else:
                    self._deleteRpmPackage(fullname)
                    log("Older package deleted from db.", DEBUG2)
                    #log("DB after removal:", DEBUG)
                    #self.dump('namvp')
                      
        #self.dump('namvp')

        ### Since its safe, add this rpm to the database ###
        log("Adding %s" % file, VERBOSE)

        # add to general list of valid rpm files
        self.rpm_index[file] = pathname

        # add to package name to filename mapping
        self.addToNameIndex(pkg_name, nvreas_list[4], file)
        
        # add this pkg-arch to the arch index
        self._shelfAppend(self.arch_index, nvre, nvreas_list)

        ## add all this packages dependancy information
        # The package name is a single, simple value 
        self._shelfAppend(self.dep_names, hdr[rpm.RPMTAG_NAME], nvre)

        # The files index is a simple, possibly multi-valued list
        for depfile in hdr[rpm.RPMTAG_FILENAMES]:
            self._shelfAppend(self.dep_files, depfile, nvre)
    
        # The provides are just plain mean.
        # complex, multi-valued list. You actually have to look at 
        # RPMTAG_PROVIDENAME[x] -> RPMTAG_PROVIDEFLAGS[x] 
        #   -> RPMTAG_PROVIDEVERSIONS[x] for each x in the 3 lists.
        # 
        # Deal with this by making a shelve. The key must be the 
        # providename of course (else we have nothing to search for).
        # The value is a list, [ NVRE, FLAG, VERSION ] all stored as 
        # strings. The NVRE is the usual name:ver:rel:epoch for the 
        # package we are dealing with. The flag and version are just 
        # the i'th fields of those rpm tags. 
        # 
        # It looks like no clients (at least up to 2.7.2) ask for 
        # the PROVIDEFLAGS or PROVIDEVERSIONS information. But I had
        # figured out how that all worked, and just added the code. I
        # strongly suspect RH will add that at some point, so leave it
        # in.

        # We make some temporary names to shorten the code. A little.
        pnames = hdr[rpm.RPMTAG_PROVIDENAME]
        pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
        pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS]

        # BUGFIX: rpm doesn't make PROVIDEFLAGS a list if there is only
        # one. Stupid library.
        if pnames != None:
            if type(pflags) != type([]):
                pflags = [pflags]
            if type(pvers) != type([]):
                pvers = [pvers]

            for i in range(len(pnames)):
                value = [nvre, pflags[i], pvers[i]]
                self._shelfAppend(self.dep_provides, pnames[i], value)

        # Now we have to do the same for obsoletes, if there are any
        onames = hdr[rpm.RPMTAG_OBSOLETENAME]
        overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
        oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
        if onames != None:
            if type(oflags) != type([]):
                oflags = [oflags]
            if type(overs) != type([]):
                overs = [overs]

            for i in range(len(onames)):
                value = [nvre, oflags[i], overs[i]]
                self._shelfAppend(self.dep_obsoletes, onames[i], value)

        # Add the rpm -> srpm link
        self.addToSourceLink(pkg_name, nvreas_list[4], hdr[rpm.RPMTAG_SOURCERPM])

        # log ("DB after add:", DEBUG)
        # self.dump('namvp')

        # Add the symlink for the GET requests
        linkname = misc.PathJoin(self.chanInfo['package_dir'],
                                 os.path.basename(pathname))
        if not os.path.exists(linkname):
            os.symlink(pathname, linkname)

        # Cache the header itself for getPackageHeader() call
        # compressed, not compressed, compressed, not compressed
        hdr_name = string.replace(file, '.rpm', '.hdr')
        filename = misc.PathJoin(self.chanInfo['headers_dir'], hdr_name)
        h_file = open(filename, 'w')
        h_file.write(hdr.unload())
        h_file.close()


    # This function is not used yet. update should have used it for 
    # "deleted" packages. Should we keep it?
    def _deletePackageNotHere(self, pkg_name):
        """ Remove RPM from the db that has been deleted from disk. """

        # FIXME:
        # do we only delete one arch?  all arches?
        # for now, I'm getting rid of all arches that don't have a disk file.
        # is an arch has a disk file, use the other delete routine

        # First, make sure the package is actually in the DB.
        if not self.dep_names.has_key(pkg_name):
            log("Ummm...  you're trying to delete something that's not here.  Go away.", DEBUG)
            return
        # find all packages that match.
        dups = []
        hits = self.dep_names[pkg_name]
        for hit in hits:
            for item in self.arch_index[hit]:
                dups.append(item)

        # Go through the dups....
        for pkg in dups:
            # ...get the filename that it was...
            filename = self.getRpmFileByPkgName(pkg[0], pkg[4])
            pathname = self.getRpmFilename(filename)
            # ... and make sure it's not there.
            if os.access(pathname, os.F_OK):
                log ("Hey, dummy - go use the other routine - the file's there.", DEBUG)
                return
            # the file's missing.  go load in the header.
            hdr_name = string.replace(pathname, '.rpm', '.hdr')
            h_file = open('%s/%s' % (self.chanInfo['headers_dir'], hdr_name), 'rb')
            hdr = rpm.headerLoad(h_file.read())
            h_file.close()
            # Generate the nvre stuff
            nvre = self._hdrToNVREString(hdr)
            nvrea = self._hdrToNVREArchString(hdr)
            nvreas_list = self._hdrToNVREASList(hdr, 0)
        
            # remove the rpm_index entry
            if not self.rpm_index.has_key(filename):
                log ("Houston, we have a problem.", MADATORY)
                log ("trying to remove a package, but didn't get something right...", MADATORY)
                return
            del self.rpm_index[filename]
            self.removeFromNameIndex(nvreas_list[0], nvreas_list[4])
            self._shelfRemove(self.arch_index, nvre, nvreas_list)
            self.removeFromSourceLink(nvreas_list[0], nvreas_list[4])
            if not self.arch_index.has_key(nvre):
                self._shelfRemove(self.dep_names, hdr[rpm.RPMTAG_NAME], nvre)
                for depfile in hdr[rpm.RPMTAG_FILENAMES]:
                    self._shelfRemove(self.dep_files, depfile, nvre)
                pnames = hdr[rpm.RPMTAG_PROVIDENAME]
                pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
                pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS]
                if pnames != None:
                    if len(pnames) == 1:
                        pflags = [pflags]
                    for i in range(len(pnames)):
                        value = [nvre, pflags[i], pvers[i]]
                        self._shelfRemove(delf.dep_provides, pnames[i], value)
                onames = hdr[rpm.RPMTAG_OBSOLETENAME]
                overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
                oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
                if onames != None:
                    if len(onames) == 1:
                        onames = [onames]
                    for i in range(len(onames)):
                        value = [nvre, oflags[i], overs[i]]
                        self._shelfRemove(self.dep_obsoletes, onames[i], value)
            # remove the cached header - everything should be completely gone now
            os.remove('%s/%s' % (self.chanInfo['headers_dir'], hdr_name))
            

    def _deleteRpmPackage(self, pathname):
        """ Remove an rpm from the database. """

        # we use the rpm file itself (actually, the header) to drive 
        # the removal process.
        (hdr, isSource) = self._getHeaderFromFilename(pathname)

        if isSource:
            return
        
        rpm_size = str(os.stat(pathname)[stat.ST_SIZE])
        file = os.path.basename(pathname)
        log("Removing %s" % file, VERBOSE)
        
        # Just generate these strings once
        nvre = self._hdrToNVREString(hdr)
        nvrea = self._hdrToNVREArchString(hdr)
        nvreas_list = self._hdrToNVREASList(hdr, rpm_size)

        # database sanity checking
        if not self.rpm_index.has_key(file):
            log("Could not remove %s - not in database." % file, MANDATORY)
            return

        # Remove this package from the database
        # Remove the rpmname -> pathname mapping
        # Recall rpm_index and src_index are NOT shelves
        #  neither is name_index
        del self.rpm_index[file]
        self.removeFromNameIndex(nvreas_list[0], nvreas_list[4])

        # remove from the arch index
        self._shelfRemove(self.arch_index, nvre, nvreas_list)

        # remove the srpm link information
        self.removeFromSourceLink(nvreas_list[0], nvreas_list[4])

        ## remove all the dependancy information
        # Reference counting bugfix:
        # Can't delete the deps entries until the corrosponding 
        #    arch_index entry is completely gone.
        if not self.arch_index.has_key(nvre):
            self._shelfRemove(self.dep_names, hdr[rpm.RPMTAG_NAME], nvre)
        
            # The files index is a simple, possibly multi-valued list
            for depfile in hdr[rpm.RPMTAG_FILENAMES]:
                self._shelfRemove(self.dep_files, depfile, nvre)
    
            # See _addRpmPackage() for why the provides suck so much
            # We make some temporary names to shorten the code. A little.
            pnames = hdr[rpm.RPMTAG_PROVIDENAME]
            pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
            pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS]
    
            # BUGFIX: rpm doesn't make PROVIDEFLAGS a list if there is only
            # one. Stupid library.
            if pnames != None:
                if len(pnames) == 1:
                    pflags = [pflags]
    
                for i in range(len(pnames)):
                    value = [nvre, pflags[i], pvers[i]]
                    self._shelfRemove(self.dep_provides, pnames[i], value)
    
            # We go through similar hoops for obsoletes as for provides
            onames = hdr[rpm.RPMTAG_OBSOLETENAME]
            overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
            oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
    
            # BUG?!?: I don't know whether rpmlib has the same bug for single
            # obsoletes as it does for provides. we assume it does for now...
            if onames != None:
                if len(onames) == 1:
                    oflags = [oflags]
    
                for i in range(len(onames)):
                    value = [nvre, oflags[i], overs[i]]
                    self._shelfRemove(self.dep_obsoletes, onames[i], value)

        # Remove the symlink
        os.remove(misc.PathJoin(self.chanInfo['package_dir'], 
                                os.path.basename(pathname)))

        # Remove the cached header 
        hdr_name = string.replace(file, '.rpm', '.hdr')
        os.remove('%s/%s' % (self.chanInfo['headers_dir'], hdr_name))


    def _addSrcDir(self, dirname):
        """Add a directory of source RPMS to the channel. """

        if not os.path.isdir(dirname):
            log("Warning: %s was not a valid dir" % dirname, MANDATORY)
            return

        for file in os.listdir(dirname):
            pathname = misc.PathJoin(dirname, file)
            self._addSrcPackage(pathname, file)


    def _addSrcPackage(self, pathname, file):
        # FIXME: We should remove older versions of the SRPMs just as we
        # do with binary RPMS, and we should probably enforce that there is
        # an SRPM for each and every RPM if there is one for any.

        (hdr, isSrc) = self._getHeaderFromFilename(pathname, 0)
        # if we're not an SRPM, exit.
        if not isSrc:
            return
        # if we don't have a valid header, exit
        if hdr == None:
            return

        # we have a valid SRPM, now add it to the index blindly.
        log ('Adding SRPM %s with path %s' % (file,pathname), DEBUG2)
        self.src_index[file] = pathname

        # in 1.3.10 - we may not need the index anymore?
        linkname = misc.PathJoin(self.chanInfo['packagesource_dir'],
                                 os.path.basename(pathname))

        if not os.path.exists(linkname):
            os.symlink(pathname, linkname)
        
    
    def _listToNVREString(self, list):
        """ Convert a NVRE* list to a string equivalent. 
    
        Extra elements (arch, size, favorite color) are ignored. 

        """

        epoch = list[3]
        if epoch == None:
            epoch = ''
        else:
            epoch = str(epoch)
    
        return string.join((list[0], list[1], 
                            list[2], epoch), self._SEP)


    def _listToNVREArchString(self, list):
        """ Convert a NVREA* list to a string equivalent.
    
        Extra elements (arch, size, favorite color) are ignored.

        """

        epoch = list[3]
        if epoch == None:
            epoch = ''
        else:
            epoch = str(epoch)
    
        return string.join((list[0], list[1], 
                            list[2], epoch, list[4]), self._SEP)


    def _hdrToNVREString(self, hdr):
        """ Convert a header to Name:Version:Release:Epoch string. """

        epoch = hdr[rpm.RPMTAG_EPOCH]
        if epoch == None:
            epoch = ''
        else:
            epoch = str(epoch)
    
        return string.join((hdr[rpm.RPMTAG_NAME], hdr[rpm.RPMTAG_VERSION], 
                            hdr[rpm.RPMTAG_RELEASE], epoch), self._SEP)


    def _hdrToNVREArchString(self, hdr):
        """ Convert a header to Name:Version:Release:Epoch:Arch string. """

        epoch = hdr[rpm.RPMTAG_EPOCH]
        if epoch == None:
            epoch = ''
        else:
            epoch = str(epoch)
    
        return string.join((hdr[rpm.RPMTAG_NAME], hdr[rpm.RPMTAG_VERSION], 
                            hdr[rpm.RPMTAG_RELEASE], epoch,  
                            hdr[rpm.RPMTAG_ARCH]), self._SEP)
                                  

    def _hdrToNVREASList(self, hdr, rpm_size):
        """ Convert a header to Name:Version:Release:Epoch:Arch:Size list. """

        epoch = hdr[rpm.RPMTAG_EPOCH]
        if epoch == None:
            epoch = ''
        else:
            epoch = str(epoch)
    
        return [ hdr[rpm.RPMTAG_NAME], hdr[rpm.RPMTAG_VERSION], 
                 hdr[rpm.RPMTAG_RELEASE], epoch,  
                 hdr[rpm.RPMTAG_ARCH], rpm_size ]
                                  

    def _shelfAppend(self, shelf, key, value):
        """ Generic function to update a list stored in a shelf """
        if shelf.has_key(key):
            # don't do a double add
            if value not in shelf[key]:
                shelf[key] = shelf[key] + [value]
        else:
            shelf[key] = [value]


    def _shelfRemove(self, shelf, key, value):
        """ Generic function to remove an item from a list stored in a shelf """
        
        old_list = shelf[key]
        old_list.remove(value)

        if len(old_list):
            shelf[key] = old_list
        else:
            del shelf[key]


#     def _compareVersion(pkg1, pkg2):
# 
#         if pkg1[3] == "":
#             pkg1[3] = None
#         else:
#             pkg1[3] = "%s" % pkg1[3]
#             
#         if pkg2[3] == "":
#                 pkg2[3] = None
#         else:
#             pkg2[3] = "%s" % pkg2[3]
#             
#         return rpm.labelCompare((pkg1[3], pkg1[1], pkg1[2]),
#                                 (pkg2[3], pkg2[1], pkg2[2]))


def _orderArchs(item1, item2):
    if item1[4] == item2[4]: 
        return 0
    if item1[4] == 'i386':
        return -1
    if item2[4] == 'i386':
        return 1
    if item1[4] == 'noarch':
        return -1
    # else we don't care
    return 1


def _main():

    print "This needs updating - use cadmin for testing "
    sys.exit(1)

if __name__ == '__main__':
    _main()
    

## END OF LINE ##
