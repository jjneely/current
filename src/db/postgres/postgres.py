""" Implementation of the PostgreSQL backend for Current"""

# We NEVER want to pass a cursor object outside of this module.  NEVER.

import pgdb
import schema
from db.currentdb import CurrentDB
import sys
from logger import *
import rpm_wrapper
import string 
import os
import os.path
import time
import gzip
import xmlrpclib
import archtab
import pprint

class PostgresDB(CurrentDB):
    def __init__(self):
        # What to put here?
        self.conn = None
        self.cursor = None   # not sure if this is ideal...
        self.rpmWrapper = rpm_wrapper.rpmWrapper()

    def __del__(self):
        self.cursor.close()
        self.cursor = None
        self.conn.close()
        self.conn = None

    def initdb(self, config):
        # We don't do normal loggin here, we use prints, as this is
        # currently handled locally (no pun intended).
        CurrentDB.initdb(self, config)

        try:
            self.conn = pgdb.connect(config['db_dsn'])
            print "Connected vis DSN"
        except:
            try:
                self.conn = pgdb.connect(user=config['db_user'], host=config['db_host'], password=config['db_pass'], database=config['db_name'])
                print "Connected via user, password, host, database"
            except Exception, e:
                print "Could not connect to database!"
                print "\n";
                print "Please make sure your Postgres instance is configured to allow TCP/IP"
                print "connections from this host with the specified username and password to"
                print "the specified database."
                sys.exit(0)

        print "Connection obtained.  Going to create database tables."
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(schema.INITDB)
        except Exception, e:
            print "Error creating database tables!  Perhaps you need to drop and"
            print "recreate this database."
            print e
            sys.exit(0)        
        self.conn.commit()
        print "Database table create commited.  Initdb done.  You can now start the"
        print "actual Current server on this host and populate the channel information"
        print "with cadmin."

    def connect(self, config):
        # We'll definitely need loggin here, but I've yet to figure out
        # how to make that work sanely.
        log("Obtaining connection", TRACE)
        if ( self.conn != None ):
            log("Connection already exists!", TRACE)
            return
        try: 
            self.conn = pgdb.connect(config['db_dsn'])
            log("Connection obtained via DSN", TRACE)
        except:
            self.conn = pgdb.connect(user=config['db_user'], host=config['db_host'], password=config['db_pass'], database=config['db_name'])
            log ("Connection via user/password", TRACE)

    def disconnect(self):
        if ( self.cursor != None ):
            self.cursor.close()
            self.cursor = None
        if ( self.conn != None ):
            self.conn.close()
            self.conn = None

    def makeChannel(self, config, channel):
        logfunc(locals(), TRACE)
        self.cursor = self.conn.cursor()

        # FIXME: Need to check for duplicate channel creation.
        # Labels must be unique, everything else can be duplicated.
        # We get compatible (as opposed to parent / child) channels for free
        # from this scheme...  cool.

        if (channel.has_key('parent') ):
            log("Creating a child channel", TRACE)
            # First, grab the id of the parent channel specified.
            self.cursor.execute("""select channel_id from CHANNEL where
                label = '%s'""" % (channel['parent'],) )
            res = self.cursor.fetchall()
            if (len(res) != 1):
                return "Better check your database...  you have duplicate labels..."
            chid = res[0][0]
            # Then, grab the parent channel's arch and release
            self.cursor.execute("""select arch, osrelease from CHANNEL where
                channel_id = '%s'""" % (chid,) )
            res = self.cursor.fetchall()
            if ( len(res) != 1):
                return "You have real problems - duplicate channel id's."
            arch = res[0][0]
            rel = res[0][1]
            # Last, add the info to the DB.
            self.cursor.execute("""insert into CHANNEL
                    (name, label, arch, osrelease, description, lastupdate, parentchannel_id)
                    values ('%s', '%s', '%s', '%s', '%s', '%s', '%s')""" %
                        (channel['name'],
                         channel['label'],
                         arch,
                         rel,
                         channel['desc'],
                         time.strftime("%Y%m%d%H%M%S", time.gmtime() ),
                         chid ) )

        else:
            # Check for duplicate top-level channel creations here?
            # Yes, but later.
            log("Creating new top channel", TRACE)
            self.cursor.execute("""insert into CHANNEL
                    (name, label, arch, osrelease, description, lastupdate)
                    values ('%s', '%s', '%s', '%s', '%s', '%s')""" %
                        (channel['name'],
                         channel['label'],
                         channel['arch'],
                         channel['release'],
                         channel['desc'],
                         time.strftime("%Y%m%d%H%M%S", time.gmtime() ) ) )
        self.conn.commit()
        log("New channel created and committed.", TRIVIA)

        # Now create the directories and such and so.
        webdir = os.path.join(config['current_dir'], 'www')
        chan_dir = os.path.join(webdir, channel['label'])
        if ( not os.access(chan_dir, os.W_OK) ):
            os.mkdir(chan_dir)
            os.mkdir(os.path.join(chan_dir, 'getObsoletes'))
            os.mkdir(os.path.join(chan_dir, 'getPackage'))
            os.mkdir(os.path.join(chan_dir, 'getPackageHeader'))
            os.mkdir(os.path.join(chan_dir, 'getPackageSource'))
            os.mkdir(os.path.join(chan_dir, 'listPackages'))

        log("New channel and dirs created.", DEBUG2)

        return "ok"

    def addDir(self, channame, dirname, binary=1):
        # If binary = 1 (the default), we assume this is a directory of
        # binary RPMS.  That's what the indicator is there for.
        logfunc(locals(), TRACE)
        if (self.cursor == None):
            self.cursor = self.conn.cursor()
        elif ( self.cursor.description == None ):
            self.cursor = self.conn.cursor()        
        self.cursor.execute("select channel_id from channel where label = '%s'"
                % (channame,) )
        reslt = self.cursor.fetchall()
        if ( len(reslt) != 1 ):
            return "No channel or too many channels with given name!"
        chanid = int(reslt[0][0])
        self.cursor.execute("""insert into channel_dir 
                (channel_id, dirpathname, is_bin_dir) 
                values
                (%d, '%s', '%s')"""
                % (chanid, dirname, str(binary)) )
        self.conn.commit()
        log("Directory/ies added to channel", DEBUG2)
        return "ok"

    def scanChannel(self, config, channel):
        # This would be a good place to drop the indexes...  then recreate them
        # when we're all done.  We don't do that yet.
        result = {}
        logfunc(locals(), TRACE)
        self.cursor = self.conn.cursor()
        # Update the channel modification time FIRST.
        self.cursor.execute("""update channel set lastupdate='%s'
                    where channel.label = '%s'"""
                    % ( time.strftime("%Y%m%d%H%M%S", time.gmtime() ), channel ) )
        # Need to always scan SRPMS (if any) first.  Otherwise, we have to do
        # a two-pass import, which we don't want to do.
        result['src'] = self._scanChannelSrc(channel)
        log("Src dirs scanned", DEBUG2)
        result['bin'] = self._scanChannelBin(config, channel)
        log("Bin dirs scanned", DEBUG2)
        result['chkdeletedfiles'] = self._scanForFiles(channel)
        log("Files scanned", DEBUG2)
        self.conn.commit()
        self.cursor = self.conn.cursor()
        result['setactive'] = self._setActiveElems(channel)
        log("Active elements (RPMS) set", DEBUG2)
        result['populatedirs'] = self._populateChannelDirs(config, channel)
        log("Channel dirs populated", DEBUG2)
        return result

    def _scanChannelSrc(self, channel):
        # We assume that all directories have been sanity checked (i.e. they
        # exist and are readble, etc) when they were added to the tables, so
        # we don't waste time doing that again here.  We just add a metric ton
        # of information to the database...
        # QUESTION: Is this /all/ a single transaction, or is /each/ RPM/SRPM
        #   a single transaction?
        # IMHO:  *shrug*  I dunno...
        result = {}
        # first, select the binary dirs
        self.cursor = self.conn.cursor()
        self.cursor.execute("""select dirpathname from CHANNEL_DIR
            inner join CHANNEL on (channel.channel_id = channel_dir.channel_id)
            where channel.label = '%s' 
            and channel_dir.is_bin_dir = '0'""" % (channel,) )
        query = self.cursor.fetchall()
        incr_reslt = 1
        for row in query:
            log("Going to scan SRC dir %s for channel %s" % (row[0], channel), TRIVIA)
            incr_reslt = incr_reslt and (0 != self._scanSrcDir(channel, row[0]))
        if ( incr_reslt != 1 ):
            result['status'] = 'failed'
        else:
            result['status'] = 'ok'
        return result

    def _scanSrcDir(self, channel, dir):
        result = 1

        self.cursor = self.conn.cursor()
        for file in os.listdir(dir):
            log("Scanning file %s" % (file,), TRACE)
            pathname = os.path.join(dir, file)
            rpm_info = self.rpmWrapper.getRpmInfo(pathname)
            if (rpm_info == None or not rpm_info['issrc']):
                log("Not a src rpm.", TRACE)
                continue
            srpm_id = self._getSrpmId(file)
            if not srpm_id:
                self.cursor.execute("""insert into srpm (filename, pathname)
                                values
                                ('%s', '%s') """ %
                                (file, pathname) )
            srpm_id = self._getSrpmId(file)
            result = result and ( 0 != srpm_id )
            log("File scan result: %s" % (result,), TRACE)
        self.conn.commit()
        return result



    def _scanChannelBin(self, config, channel):
        # We assume that all directories have been sanity checked (i.e. they
        # exist and are readble, etc) when they were added to the tables, so
        # we don't waste time doing that again here.  We just add a metric ton
        # of information to the database...
        # QUESTION: Is this /all/ a single transaction, or is /each/ RPM/SRPM
        #   a single transaction?
        # IMHO:  *shrug*  I dunno...
        logfunc(locals(), TRIVIA)
        result = {}
        # first, select the binary dirs
        self.cursor = self.conn.cursor()
        self.cursor.execute("""select dirpathname from CHANNEL_DIR
            inner join CHANNEL on (channel.channel_id = channel_dir.channel_id)
            where channel.label = '%s' 
            and channel_dir.is_bin_dir = '1'""" % (channel,) )
        query = self.cursor.fetchall()
        incr_reslt = 1
        for row in query:
            log ("Scanning bin dir %s of channel %s" % (row[0], channel), TRIVIA)
            incr_reslt = incr_reslt and ( 0 != self._scanDirToChannel(config, channel, row[0]) )

        if ( incr_reslt != 1 ):
            result['status'] = 'failed'
        else:
            result['status'] = 'ok'
        return result


    def _scanDirToChannel(self, config, channel, dir):
        result = 1
        log("scanning directory %s" % (dir,) )
        for file in os.listdir(dir):
            pathname = os.path.join(dir, file)
            result = result and ( 0 != self._addRpmPackage(config, pathname, channel) )
        log ("returning result of %d for dir %s" % (result, dir) )
        return result

    def _addRpmPackage(self, config, path, channel):
        self.cursor = self.conn.cursor()
        filename = os.path.basename(path)
        rpm_info = self.rpmWrapper.getRpmInfo(path)

        if (self.cursor == None):
            self.cursor = self.conn.cursor()
        elif (self.cursor.description == None):
            self.cursor = self.conn.cursor()

        # sanity check:
        if (None == rpm_info):
            return 1
        # Check to see if the package is already in the DB before we do something stupid.
        if ( self._packageInDB(rpm_info) ):
            log ("Package already in DB - not scanning.", TRIVIA)
            return 1
 
        log("Adding RPM %s to channel %s" % (path, channel), TRIVIA)

        # Get the channel ID:
        self.cursor.execute("""select channel_id from CHANNEL
                where label = '%s' """ % (channel,))
        chreslts = self.cursor.fetchall()
        if (len(chreslts) != 1 ):
            log("no results for channel pull!")
            return 0
        ch_id = chreslts[0][0]

        log("Inserting package information.", TRACE)
        package_id = self._insertPackageTable(rpm_info)
        if ( package_id == 0 ):
            # we have a problem.  return it.
            log("package_id problem")
            return 0
        # the next call returns 0 on failure, otherwise positive non-zero
        log("Inserting RPM information.", TRACE)
        rpm_id = self._insertRpmTable(rpm_info, package_id, ch_id)
        if not rpm_id:
            log("RPM %s failed." % (path,) )

        # Put the header file into place
        log("Creating header file.", TRACE)
        self._createHeaderFile(config, channel, filename, rpm_info['hdr'])

        # We return the success of the rpm table insert - pos non-0 is good
        self.conn.commit()
        return rpm_id

    def _getPackageId(self, name, version, release, epoch):
        sql = """ select package_id from package
                where package.pkgname = %s
                and package.version = %s
                and package.release = %s
                and package.epoch = %s"""
        args = (name, version, release, epoch)
        self.cursor.execute(sql, args)
        row = self.cursor.fetchall()
        if ( len(row) > 1 ):
            raise Exception, "EEEEPPPPP!!!! db.db._getPackageId()"
        if ( len(row) == 0 ):
            return None
        else:
            return int(row[0][0])

    def _packageInDB(self, rpm_info):
        pid = self._getPackageId(rpm_info['name'], rpm_info['version'],
                                rpm_info['release'], rpm_info['epoch'])
        if (pid != 0 ):
            self.cursor = self.conn.cursor()
            sql = """ select rpm_id from rpm where rpm.package_id = '%d'
                                    and rpm.arch = '%s'""" % (pid, rpm_info['arch'])
            self.cursor.execute(sql)
            results=  self.cursor.fetchall()
            if (len(results) > 1):
                raise Exception, "EEEEP! db.db._packageInDB()"
            if ( len(results) == 0):
                return 0
            else:
                return 1
        return pid
        
    def _insertPackageTable(self, rpm_info):
        package_id = self._getPackageId(rpm_info['name'], rpm_info['version'],
                                rpm_info['release'], rpm_info['epoch'])

        if not package_id:
            self.cursor.execute("""insert into package
                        (pkgname, version, release, epoch)
                        values
                        ('%s', '%s', '%s', '%s')""" %
                        (rpm_info['name'], rpm_info['version'],
                         rpm_info['release'], rpm_info['epoch']) )

        package_id = self._getPackageId(rpm_info['name'], rpm_info['version'],
                                rpm_info['release'], rpm_info['epoch'])

        assert package_id

        return package_id
                
    def _getRpmId(self, path):
        self.cursor.execute("""select rpm_id from rpm
                        where rpm.pathname = '%s'""" % (path,) )
        result = self.cursor.fetchall()
        assert ( len(result) <= 1 )
        if (len(result) == 0 ):
            return None
        else:
            return int(result[0][0])


    def _getSrpmId(self, filename):
        self.cursor.execute("""select srpm_id from srpm
                            where srpm.filename = '%s'""" % (filename,) )
        result = self.cursor.fetchall()
        if ( len(result) == 0) :
            return None
        else:
            return int(result[0][0])


    def _insertRpmTable(self, rpm_info, package_id, ch_id):
        rpm_id = self._getRpmId(rpm_info['pathname'])
        srpm_id = self._getSrpmId(rpm_info['srpm']) or 0

        if not rpm_id:
            self.cursor.execute("""insert into rpm
                                (package_id, srpm_id, pathname, arch, size,
                                 original_channel_id, active_channel_id)
                                values
                                (%d, %d, '%s', '%s', %d, %d, %d)""" %
                                (package_id, srpm_id, rpm_info['pathname'],
                                 rpm_info['arch'], int(rpm_info['size']),
                                 ch_id, 0) )

        rpm_id = self._getRpmId(rpm_info['pathname'])
        assert rpm_id
        # We'll need to update the provides and obsoletes tables here...

        self._insertObsoletes(rpm_id, rpm_info)
        self._insertProvides(rpm_id, rpm_info)

        return rpm_id

    def _insertObsoletes(self, rpm_id, rpm_info):
        for obs in rpm_info['obsoletes']:
            self.cursor.execute("""insert into rpmobsolete
                            (rpm_id, name, flags, vers)
                            values
                            ( %d, '%s', '%s', '%s')""" % 
                            (rpm_id, obs[0], obs[1], obs[2]) )
 
    def _insertProvides(self, rpm_id, rpm_info):
        for prov in rpm_info['dep_provides']:
            self.cursor.execute("""insert into rpmprovide
                            (rpm_id, name, flags, vers)
                            values
                            ( %d, '%s', '%s', '%s')""" % 
                            (rpm_id, prov[0], prov[1], prov[2]) )


    def _scanForFiles(self, channel):
        result = 1
        self.cursor.execute("""select pathname from RPM
                inner join channel on (channel.channel_id = rpm.original_channel_id)
                where (channel.label = '%s')""" % (channel,) )
        query = self.cursor.fetchall()
        for row in query:
            filename = row[0]
            result = result and os.access(filename, os.R_OK)
        return result

    def _setActiveElems(self, channel):
        # This is what sets which RPMS are active.  I'tll be fun to diagnose...
        # First, get a list of unique pkg names:
        self.cursor = self.conn.cursor()
        self.cursor.execute(""" select distinct on (pkgname) pkgname from package
                    inner join rpm on (package.package_id = rpm.package_id)
                    inner join channel on (channel.channel_id = rpm.original_channel_id)
                    where channel.label = '%s'""" % (channel,) )
        pkgs = []
        newest_ids = []
        query = self.cursor.fetchall()
        for row in query:
            pkgs.append(row[0])

        for pkg in pkgs:
            for id in self._findNewest(channel, pkg):
                newest_ids.append(id)

        self.cursor.execute("""select channel_id from channel 
                    where channel.label = '%s'""" %
                    (channel,) )
        chqry = self.cursor.fetchall()
        assert (len(chqry) == 1 )
        chid = int(chqry[0][0])
        # Set everything in this channel inactive to amke sure we don't have
        # any stale active records:
        self.cursor.execute("""update rpm set active_channel_id = 0
                where rpm.original_channel_id = %d""" % (chid,) )
        self.conn.commit()
        self.cursor = self.conn.cursor()
        for id in newest_ids:
            log('setting rpmid %s active' % id)
            self.cursor.execute("""update rpm set active_channel_id = %d
                    where rpm.rpm_id = %d""" % (chid, id) )

        self.conn.commit()
        return "done"

    def _findNewest(self, channel, pkg):
        self.cursor.execute("""select pkgname, version, release, epoch from PACKAGE
                    inner join rpm on (package.package_id = rpm.package_id)
                    inner join channel on (rpm.original_channel_id = channel.channel_id)
                    where package.pkgname = '%s' and channel.label = '%s'""" %
                    (pkg, channel) )
        query = self.cursor.fetchall()

        # Sort the list
        # We construct the lambda evilly so that it's actually sorted in 
        # reverse order...
        query.sort(lambda x,y: rpm_wrapper.rpmVerCmp( (y[3], y[1], y[2]), (x[3], x[1], x[2]) ) )

        # Now update the RPM table appropriately.
        self.cursor.execute("""select rpm_id from RPM
                    inner join package on (package.package_id = rpm.package_id)
                    inner join channel on (rpm.original_channel_id = channel.channel_id)
                    where package.pkgname = '%s'
                        and package.version = '%s'
                        and package.release = '%s'
                        and package.epoch = '%s' 
                        and channel.label = '%s'""" %
                    (query[0][0], query[0][1], query[0][2], query[0][3], channel) )
        queryret = self.cursor.fetchall()
        retval = []
        for row in queryret:
            retval.append(row[0])
        return retval



    def _createHeaderFile(self, config, channel, filename, headerBlob):
        # This routine just creates the header file in the www tree
        hdr_name = string.replace(filename, '.rpm', '.hdr')
        pathname = os.path.join(config['current_dir'], 'www', channel, 'getPackageHeader', hdr_name)
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        h_file = open(pathname, 'wb')
        h_file.write(headerBlob.unload())
        h_file.close()

    def _populateChannelDirs(self, config, channel):
        logfunc(locals(), DEBUG2)
        results = {}
        self.cursor.execute("""select lastupdate from channel where
                    channel.label = '%s'""" % (channel,) )
        qry = self.cursor.fetchall()
        # Should only be one channel...
        assert ( len(qry) == 1)
        updatefilename = qry[0][0]

        # First, populate the listPackages directory.
        log("Grabbing listPackages information", TRIVIA)
        self.cursor.execute("""select package.pkgname, package.version,
                package.release, package.epoch, rpm.arch, rpm.size from
                package, rpm
                inner join channel on (rpm.active_channel_id = channel.channel_id)
                where channel.label = '%s'
                and package.package_id = rpm.package_id
                order by package.pkgname""" % (channel,) )
        query = self.cursor.fetchall()
        # query should now contain the list of lists we (almost) want.
        for row in query:
            row[5] = "%d" % (row[5],)
            row.append(channel)
        # now query should contain exactly what we want. (wow, that was cool...)
        query = (query,)
        log("Creating listPackages file", DEBUG2)
        pathname = os.path.join(config['current_dir'], 'www', channel, 'listPackages', updatefilename )
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        pl_file = gzip.GzipFile(pathname, 'wb', 9)
        str = xmlrpclib.dumps(query, methodresponse=1)
        pl_file.write(str)
        pl_file.close()        
        log("listPackages file created successfully", DEBUG)
        results['listPackages'] = "ok"
        
        # Now populate the getObsoletes directory.
        log("Grabbing getObsoletes information", TRIVIA)
        self.cursor.execute("""select package.pkgname, package.version,
                package.release, package.epoch, rpm.arch,
                rpmobsolete.name, rpmobsolete.flags, rpmobsolete.vers
                from package, rpmobsolete, rpm
                inner join channel on (rpm.active_channel_id = channel.channel_id)
                where channel.label = '%s'
                and package.package_id = rpm.package_id
                and rpm.rpm_id = rpmobsolete.rpm_id 
                order by package.pkgname""" % (channel,) )
        query = self.cursor.fetchall()
        for row in query:
            for item in row:
                if ( item == None ):
                    item = ''
                if ( type(item) != type('') ):
                    item = str(item)
        query = (query,)
        log("Creating getObsoletes file", DEBUG2)
        pathname = os.path.join(config['current_dir'], 'www', channel, 'getObsoletes', updatefilename )
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        pl_file = gzip.GzipFile(pathname, 'wb', 9)
        str = xmlrpclib.dumps(query, methodresponse=1)
        pl_file.write(str)
        pl_file.close()
        log("getObsoletes file created succefully", DEBUG)
        results['getObsoletes'] = "ok"

        # Now populate getPackageSource
        log("grabbing getPackageSource information", TRIVIA)
        self.cursor.execute("""select distinct on (srpm.filename) srpm.filename, srpm.pathname from srpm
                inner join rpm on (srpm.srpm_id = rpm.srpm_id)
                inner join channel on (rpm.active_channel_id = channel.channel_id)
                where channel.label = '%s'""" % (channel,) )
        query = self.cursor.fetchall()
        dpath = os.path.join( config['current_dir'], 'www', channel, 'getPackageSource')
        log("Unlinking old files...", TRIVIA)
        for file in os.listdir(dpath):
            os.unlink( os.path.join(dpath, file) )
        log("Creating symlinks...", DEBUG2)
        for row in query:
            src = row[1]
            dst = os.path.join(dpath, row[0])
            os.symlink(src, dst)
        log("getPackageSource synlinks created", DEBUG)
        results['getPackageSource'] = "ok"

        # now populate getPackage
        log("grabbing getPackage information", TRIVIA)
        self.cursor.execute("""select rpm.pathname from rpm
                    inner join channel on (rpm.active_channel_id = channel.channel_id)
                    where channel.label = '%s'""" % (channel,) )
        query = self.cursor.fetchall()
        dpath = os.path.join ( config['current_dir'], 'www', channel, 'getPackage')
        log("Unlinking old files...", TRIVIA)
        for file in os.listdir(dpath):
            os.unlink( os.path.join (dpath, file) )
        log("Creating getPackage symlinks...", DEBUG2)
        for row in query:
            dir = os.path.join(dpath, os.path.basename(row[0]) )
            try:
                os.symlink(row[0], dir)
            except OSError, error:
                log("OS Error number %s occurred - why?" % error, DEBUG)
        log("getPackage symlinks created", DEBUG)
        results['getPackage'] = "ok"

        # getPackageHeader ought to already be populated, so we're done.
        return results

    # Here starts up2date API calls.
    def getCompatibleChannels(self, arch, release):
        # Need to return a dict with label and last modified of all compatible
        # channels (other information okay but not necessary)

        # get the canonical architecture.
        carch = archtab.getCannonArch(arch)

        log ("arch: %s, rel: %s" % (carch, release) )
        self.cursor = self.conn.cursor()
        self.cursor.execute("""select name, label, arch, description, 
                    lastupdate from channel
                    where arch = '%s'
                    and osrelease = '%s'"""
                    % (carch, release) )
        query = self.cursor.fetchall()
        log ("found: %s" % ( str(query), ) )
        chanList = []
        # FIXME: get parent channel info in there.
        for row in query:
            chan = {}
            chan['name'] = row[0]
            chan['label'] = row[1]
            chan['arch'] = row[2]
            chan['description'] = row[3]
            chan['lastupdate'] = row[4]
            chan['parent_channel'] = ''
            chanList.append(chan)

        return chanList

    def solveDependancy(self, label, arch, unknown):
        # We only solve for a single dependency at a time.
        logfunc(locals())
        # First, find the channel.
        self.cursor.execute("""select channel_id from CHANNEL
                where label = '%s'"""
                % ( label, ) )
        channels = self.cursor.fetchall()
        if ( len(channels) != 1 ):
            log ("crap...  no active channels found in solveDependencies...", DEBUG2)
            return None 
        act_ch_id = channels[0][0]
        # Find the RPM ID of the package in the active channel
        self.cursor.execute("""select distinct on (rpmprovide.rpm_id) 
                    rpmprovide.rpm_id from rpmprovide
                    inner join RPM on (rpmprovide.rpm_id = rpm.rpm_id)
                    where rpm.active_channel_id = '%s'
                    and name = '%s'
                    """ % (act_ch_id, unknown) )
        rpms = self.cursor.fetchall()
        if ( len(rpms) == 0 ):
            log ("Could not find active RPM solving for unknown %s" % (unknown), DEBUG2)
            return None
        if ( len(rpms) > 1 ):
            log ('More than one possible solution for dep %s - potential problem.' % (unknown,) )
        # Just take the first one, in case there's more than one.
        id = rpms[0][0]

        # Grab the active package
        self.cursor.execute("""select p.pkgname, p.version, p.release,
                p.epoch, r.arch, r.size
                from PACKAGE as p, RPM as r
                where p.package_id = r.package_id
                and r.rpm_id = '%s'"""
                % (id,) )
        result = self.cursor.fetchall()
        if ( len(result) != 1 ):
            log('Crap.  %d results returned.' % (len(results),) )
            return None
        logfunc(locals())
        log ("up2date.solveDependency is returning %s" % result, DEBUG)
        if ( type(result[0]) != type([]) ):
            result = [result]
        return result            

    def getLastUpdate(self, release, arch):
        # This routine added for APPLET functionality - simply gets the most
        # recent update time of the most recently updated channel for the
        # given release / arch combination.
        # Get a connection
        self.cursor = self.conn.cursor()

        # First, get the base arch, since arch may not be a canonical.
        carch = archtab.getCannonArch(arch)

        # Now, get all the channels of given carch / release, sorted by
        # update time.
        self.cursor.execute("""select lastupdate from CHANNEL
                    where arch = '%s'
                    and osrelease = '%s'
                    order by lastupdate desc"""
                    % (carch, release) )
        result = self.cursor.fetchall()
        self.conn.commit()
        if ( len(result) < 1 ):
            return -1
        else:
            return result[0][0]

    def listAppletPackages(self, release, arch):
        # This routine will return a list of all packages in all compatible
        # channels - it's designed for use with the APPLET code.
        # FIXME: We will need to somehow determine which channels a given
        # client is subscribed to at a later point...  how to do this, if
        # uuid is unrelated to anything?  dunno...

        # Get a cursor
        self.cursor = self.conn.cursor()
        self.cursor.execute(""" select pkgname, version, release, epoch
                from package
                inner join rpm on (rpm.package_id = package.package_id)
                inner join channel on (channel.channel_id = rpm.active_channel_id)
                where channel.arch = '%s' and channel.osrelease = '%s'
                order by pkgname"""
                % (arch, release) )
        result = self.cursor.fetchall()
        log ('grabbed %s packages' % len(result) )
        return result


