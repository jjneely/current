""" Wrapper module around rpmlib.

Because the rpm module has so many quirks that may affect current, we 
encapsulate all the direct rpm interactions in this module, so that the 
backends and other code see a single, sane, consistent interface.

Current has also had several rpm related bugs, so bug fixes here will 
automatically fix all the backends.

"""

import os
import os.path
import stat
import types 
import rpm

# namespace silliness
# RPM is specific to current. All current is interested in is various 
# fields, the RPMTAG_* fields. tagnames are just the RPMTAG_'s.
tagnames = {}
for key in dir(rpm):
    if key.startswith('RPMTAG_'): 
        tagnames[key[7:]] = eval('rpm.' + key)

# Now we add in current specific tags.
ct_tags = {
    'CT_FILESIZE': 10000, 'CT_PATHNAME': 10001,
    'CT_PROVIDES': 10002, 'CT_OBSOLETES': 10003,
}

for nr in ct_tags.values():
    assert nr not in tagnames.values(), "CT key conflicts with rpm key"
tagnames.update(ct_tags)

# Now reverse it:
tagvalues = {}
for (key,value) in tagnames.items():
    tagvalues[value] = key

# Make this part of our modules namespace
locals().update(tagnames)

# Make sure clients get as clean an import as we can make it
__all__ = tagnames.keys()
__all__.append('Header')

class RPMException(Exception):
    pass

class Header(object):
    def __init__(self, pathname):
        """ Note that a client is free to reach inside and grab any of 
            the pathname, file_size, hdr or is_source attributes. """

        self.pathname = pathname
        # XXX: What if we don't have permission to read the file?  Exception
        self.file_size = os.stat(pathname).st_size

        (self.hdr, self.is_source) = self._getHeaderFromFilename(pathname)

    def __getitem__(self, item):
        assert item in tagvalues, "Invalid attribute requested"

        funcname = '_get_' + tagvalues[item]
        meth = getattr(self, funcname, None)
        if meth is None:
            return self.hdr[item] 
        else: 
            return meth()


    def _get_SOURCEPACKAGE(self):
        # XXX: Why>
        # This is insane for 4.1, but required for 4.0 and earlier    
        #return not not self.is_source

        # To keep all DBs in check we just want to get an int here, force it
        # to avoild Python 2.3's bool type which I'd rather use
        return int(self.is_source)


    def _get_CT_FILESIZE(self):
        # fake our own header entries
        return self.file_size


    def _get_CT_PATHNAME(self):
        return self.pathname
        

    def _get_CT_PROVIDES(self):
        if self.hdr[rpm.RPMTAG_PROVIDENAME] == None:
            return []
        else:
            return zip(self.hdr[rpm.RPMTAG_PROVIDENAME],
                       self._get_PROVIDEVERSION(),
                       self._get_PROVIDEFLAGS())

     
    def _get_CT_OBSOLETES(self):
        if self.hdr[rpm.RPMTAG_OBSOLETENAME] == None:
            return []
        else:
            return zip(self.hdr[rpm.RPMTAG_OBSOLETENAME],
                       self._get_OBSOLETEVERSION(),
                       self._get_OBSOLETEFLAGS())

     
    def _get_EPOCH(self):
        # Library return None or an int 
        if self.hdr[rpm.RPMTAG_EPOCH] == None:
            return ''
        else:
            return str(self.hdr[rpm.RPMTAG_EPOCH])

    def _get_SERIAL(self):
        # RPMTAG_SERIAL == RPMTAG_EPOCH.  SERIAL is found first.
        # this causes problems.
        return self._get_EPOCH()


    def _get_E(self):
        # I don't know what Jeff did, but RPMTAB_E == RPMTAG_EPOCH
        # and since hunter's code looks up by the actual numeric number
        # we actually end up running this function for h[RPM.EPOCH]

        return self._get_EPOCH()


    def _get_PROVIDEVERSION(self):
        # Rpmlib screws up PROVIDEVERSION and PROVIDEFLAGS when there is 
        # only one. It gets NAME correct (list of length 1), but is broken
        # for these values.
        if type(self.hdr[rpm.RPMTAG_PROVIDEVERSION]) != types.ListType:
            return [self.hdr[rpm.RPMTAG_PROVIDEVERSION]]
        else:
            return self.hdr[rpm.RPMTAG_PROVIDEVERSION]


    def _get_PROVIDEFLAGS(self):
        if type(self.hdr[rpm.RPMTAG_PROVIDEFLAGS]) != types.ListType:
            return [self.hdr[rpm.RPMTAG_PROVIDEFLAGS]]
        else: 
            return self.hdr[rpm.RPMTAG_PROVIDEFLAGS]


    def _get_OBSOLETEVERSION(self):
        # Obsoletes suffers the same trouble as above for PROVIDES
        if type(self.hdr[rpm.RPMTAG_OBSOLETEVERSION]) != types.ListType:
            return [self.hdr[rpm.RPMTAG_OBSOLETEVERSION]]
        else:
            return self.hdr[rpm.RPMTAG_OBSOLETEVERSION]


    def _get_OBSOLETEFLAGS(self):
        if type(self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]) != types.ListType:
            return [self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]]
        else:
            return self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]


    def unload(self, dirname):
        """ Given a directory name, write just the header out as a file.

        The filename itself is not specified, as the name, version,
        release, and arch fields themselves determine it.

        """

        hdr_name = "%s-%s-%s.%s.hdr" % (self.hdr[rpm.RPMTAG_NAME],
                                        self.hdr[rpm.RPMTAG_VERSION], 
                                        self.hdr[rpm.RPMTAG_RELEASE],
                                        self.hdr[rpm.RPMTAG_ARCH])

        pathname = os.path.join(dirname, hdr_name)
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        h_file = file(pathname, 'wb')
        h_file.write(self.hdr.unload())
        h_file.close()


    def _getHeaderFromFilename(self, pathname):
        """ Open a pathname as an rpm, and retrive the header from it. """
                                                                                    
        # multiplexor function to handle the different rpm API's.
        if hasattr(rpm, 'ts'):
            return self._getHeaderFromFilename41(pathname)
        else:
            return self._getHeaderFromFilename40(pathname)
                                                                                    
                                                                                    
    def _getHeaderFromFilename40(self, pathname):
        """ Open a pathname as an rpm, using the rpm 3.0 -> 4.0 rpmlib API """

        try:
            fd = os.open(pathname, os.O_RDONLY)
            (header, isSource) = rpm.headerFromPackage(fd)
            os.close(fd)
        except:
#            logException()
            print "Warning: Could not open package %s" % pathname
            return (None, None)
            
        if header == None:
            print "Warning: Could not read package %s" % pathname
            return (None, None)
        else:
            return (header, isSource)
    
    
    def _getHeaderFromFilename41(self, pathname):
        """ Open a pathname as an rpm, using the rpm 4.1+ rpmlib API """

        try:
            ts = rpm.TransactionSet("/", rpm._RPMVSF_NOSIGNATURES)
            fd = os.open(pathname, os.O_RDONLY)
            header = ts.hdrFromFdno(fd)
            isSource = header[rpm.RPMTAG_SOURCEPACKAGE]
            os.close(fd)
        except Exception, e:
            print "Warning: Could not open package %s" % pathname
            return (None, None)
                             
        if type(isSource) == list:
            # Yes, this makes my brain hurt
            if isSource == []:
                isSource = 0 # false
            else:
                raise RPMException("Unexpected RPMTAG_SOURCEPACKAGE value")

        if header == None:
            print "Warning: Could not read package %s" % pathname
            return (None, None)
        else:                                                                                
            return (header, isSource)


# We need to figure out what to do with this routine...
def versionCompare(evr1, evr2):
    result = rpm.labelCompare(evr1, evr2)
    if (result < 0 ):
        return -1
    elif (result == 0):
        return 0
    else:
        return 1
