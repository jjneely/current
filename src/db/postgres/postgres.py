""" Implementation of the PostgreSQL backend for Current"""

import pgdb
import schema
from db.currentdb import CurrentDB
import sys
from logger import *
import RPM
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
        self.conn = None
        self.cursor = None

    def __del__(self):
        self.cursor.close()
        self.cursor = None
        self.conn.close()
        self.conn = None

    def initdb(self, config):
        CurrentDB.initdb(self, config)

        self.connect(config)

        self.cursor = self.conn.cursor()
        self.cursor.execute(schema.INITDB)
        self.conn.commit()
        log("Database table create commited.  Initdb done.", TRACE)


    def connect(self, config):
        log("Obtaining connection", TRACE)
        if self.conn:
            log("Connection already exists!", TRACE)
            return

        try:
            self.conn = pgdb.connect(user=config['db_user'], 
                                     password=config['db_pass'], 
                                     host=config['db_host'], 
                                     database=config['db_name'])
            log("Connection via user/password", TRACE)
        except Exception, e:
            log("No connection obtained!", TRACE)
            sys.exit(0)


    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None


    def makeChannel(self, config, channel):
        logfunc(locals(), TRACE)
        self.cursor = self.conn.cursor()

        # FIXME: Need to check for duplicate channel creation.
        # Labels must be unique, everything else can be duplicated.
        # We get compatible (as opposed to parent / child) channels for free
        # from this scheme...  cool.

        if (channel.has_key('parent')):
            log("Creating a child channel", TRACE)
            # First, grab the id of the parent channel specified.
            self.cursor.execute('''select channel_id from CHANNEL where
                label = %s''', (channel['parent'],))
            res = self.cursor.fetchall()
            if (len(res) != 1):
                return "Better check your database...  you have duplicate labels..."
            chid = res[0][0]
            # Then, grab the parent channel's arch and release
            self.cursor.execute('''select arch, osrelease from CHANNEL where
                channel_id = %s''', (chid,))
            res = self.cursor.fetchall()
            if (len(res) != 1):
                return "You have real problems - duplicate channel id's."
            arch = res[0][0]
            rel = res[0][1]
            # Last, add the info to the DB.
            self.cursor.execute('''insert into CHANNEL
                    (name, label, arch, osrelease, description, lastupdate, parentchannel_id)
                    values (%s, %s, %s, %s, %s, %s, %s)''', 
                        (channel['name'],
                         channel['label'],
                         arch,
                         rel,
                         channel['desc'],
                         time.strftime("%Y%m%d%H%M%S", time.gmtime()),
                         chid))

        else:
            # Check for duplicate top-level channel creations here?
            # Yes, but later.
            log("Creating new top channel", TRACE)
            self.cursor.execute('''insert into CHANNEL
                    (name, label, arch, osrelease, description, lastupdate)
                    values (%s, %s, %s, %s, %s, %s)''', 
                        (channel['name'],
                         channel['label'],
                         channel['arch'],
                         channel['release'],
                         channel['desc'],
                         time.strftime("%Y%m%d%H%M%S", time.gmtime())))
        self.conn.commit()
        log("New channel created and committed.", TRIVIA)

        # Now create the directories and such and so.
        webdir = os.path.join(config['current_dir'], 'www')
        chan_dir = os.path.join(webdir, channel['label'])
        if (not os.access(chan_dir, os.W_OK)):
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
        elif (self.cursor.description == None):
            self.cursor = self.conn.cursor()        
        self.cursor.execute('''select channel_id from CHANNEL where label = %s''',
                (channame,))
        reslt = self.cursor.fetchall()
        if (len(reslt) != 1):
            return "No channel or too many channels with given name!"
        chanid = int(reslt[0][0])
        self.cursor.execute('''insert into CHANNEL_DIR 
                (channel_id, dirpathname, is_bin_dir) 
                values
                (%d, %s, %s)''', (chanid, dirname, str(binary)))
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
        self.cursor.execute('''update CHANNEL set lastupdate=%s
                    where CHANNEL.label = %s''', 
                      (time.strftime("%Y%m%d%H%M%S", time.gmtime()), channel))
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
        self.cursor.execute('''select dirpathname from CHANNEL_DIR
            inner join CHANNEL on (CHANNEL.channel_id = CHANNEL_DIR.channel_id)
            where CHANNEL.label = %s 
            and CHANNEL_DIR.is_bin_dir = %s ''', (channel, '0'))
        query = self.cursor.fetchall()
        incr_reslt = 1
        for row in query:
            log("Going to scan SRC dir %s for channel %s" % (row[0], channel), TRIVIA)
            incr_reslt = incr_reslt and (0 != self._scanSrcDir(channel, row[0]))
        if (incr_reslt != 1):
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

            header = RPM.Header(pathname)
            if (header == None or not header[RPM.SOURCEPACKAGE]):
                log("Not a src rpm.", TRACE)
                continue
            srpm_id = self._getSrpmId(file)
            if not srpm_id:
                self.cursor.execute('''insert into SRPM (filename, pathname)
                                values
                                (%s, %s) ''', (file, pathname))
            srpm_id = self._getSrpmId(file)
            result = result and (0 != srpm_id)
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
        # reset the orig_chan table for this channel
        self.cursor = self.conn.cursor()
        self.cursor.execute('''select channel_id from CHANNEL
                        where CHANNEL.label = %s''', (channel,))
        qry = self.cursor.fetchall()
        assert (len(qry) == 1)
        chan_id = int(qry[0][0])

        self.cursor.execute('''delete from chan_rpm_orig
                        where chan_id = %d''', (chan_id,))
        self.conn.commit()
        # first, select the binary dirs
        self.cursor.execute('''select dirpathname from CHANNEL_DIR
            inner join CHANNEL on (CHANNEL.channel_id = CHANNEL_DIR.channel_id)
            where CHANNEL.label = %s 
            and CHANNEL_DIR.is_bin_dir = %s''', (channel, '0'))
        query = self.cursor.fetchall()
        incr_reslt = 1
        for row in query:
            log("Scanning bin dir %s of channel %s" % (row[0], channel), TRIVIA)
            incr_reslt = incr_reslt and (0 != self._scanDirToChannel(config, channel, row[0]))

        if (incr_reslt != 1):
            result['status'] = 'failed'
        else:
            result['status'] = 'ok'
        return result


    def _scanDirToChannel(self, config, channel, dir):
        result = 1
        log("scanning directory %s" % (dir,))
        for file in os.listdir(dir):
            pathname = os.path.join(dir, file)
            if (os.path.isdir(pathname)):
                result = result and (0 != self._scanDirToChannel(config, channel, pathname))
            if (os.path.isfile(pathname)):
                result = result and (0 != self._addRpmPackage(config, pathname, channel))
        log("returning result of %d for dir %s" % (result, dir))
        return result

    def _addRpmPackage(self, config, path, channel):
        self.cursor = self.conn.cursor()
        filename = os.path.basename(path)
        if (not filename.endswith(".rpm")):
            # not a real RPM
            return 1
        header = RPM.Header(path)
        
        if (self.cursor == None):
            self.cursor = self.conn.cursor()
        elif (self.cursor.description == None):
            self.cursor = self.conn.cursor()

        if (header.hdr == None):
            return 1
 
        # Anorther sanity check
        if (header[RPM.SOURCEPACKAGE] == 1):
            return 1
             
        log("Adding RPM %s to channel %s" % (path, channel), TRIVIA)

        # Get the channel ID:
        self.cursor.execute('''select channel_id from CHANNEL
                where label = %s ''', (channel,))
        chreslts = self.cursor.fetchall()
        if (len(chreslts) != 1):
            log("no results for channel pull!")
            return 0
        ch_id = chreslts[0][0]

        # Check for the package already in DB
        pkg_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION], 
                                    header[RPM.RELEASE], header[RPM.EPOCH])
        if pkg_id == None:
            pkg_id = self._insertPackageTable(header)

        if pkg_id == None or pkg_id == 0:
            log("Package_Id problem...")
            return 0


        rpm_id = self._insertRpmTable(header, pkg_id, ch_id)
        if not rpm_id:
            log("RPM %s failed." % (path,))

        log("Adding RPM to channel", TRACE)
        if (rpm_id == None):
            raise Exception, "Oh shit....  RPM supposed to be here, but isn't."

        self.cursor.execute('''insert into CHAN_RPM_ORIG (rpm_id, chan_id)
                            values (%d, %d) ''', (rpm_id, ch_id))

        log("RPM added to channel", TRACE)


        # Put the header file into place
        log("Creating header file.", TRACE)
        # FIXME: Abstracting this away might be nice...
        dirname = os.path.join(config['current_dir'], 'www', channel, 'getPackageHeader')
        header.unload(dirname)

        # We return the success of the rpm table insert - pos non-0 is good
        self.conn.commit()
        return rpm_id

    def _getPackageId(self, name, version, release, epoch):
        logfunc (locals())
        self.cursor.execute(''' select package_id from PACKAGE
                where pkgname = %s
                and version = %s
                and release = %s
                and epoch = %s''', (name, version, release, epoch))
        row = self.cursor.fetchall()
        if (len(row) > 1):
            raise Exception, "EEEEPPPPP!!!! db.db._getPackageId()"
        if (len(row) == 0):
            return None
        else:
            return int(row[0][0])

    def _packageInDB(self, header):
        pid = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                 header[RPM.RELEASE], header[RPM.EPOCH])
        if (pid != None and pid != 0):
            self.cursor = self.conn.cursor()
            self.cursor.execute('''select rpm_id from RPM where package_id = %d
                      and arch = %s''', (pid, header[RPM.ARCH]))
            results=  self.cursor.fetchall()
            if (len(results) > 1):
                raise Exception, "EEEEP! db.db._packageInDB()"
            if (len(results) == 0):
                return 0
            else:
                return 1
        return pid
        
    def _insertPackageTable(self, header):
        package_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                        header[RPM.RELEASE], header[RPM.EPOCH])

        if not package_id:
            self.cursor.execute('''insert into PACKAGE
                        (pkgname, version, release, epoch)
                        values
                        (%s, %s, %s, %s)''',
                        (header[RPM.NAME], header[RPM.VERSION],
                         header[RPM.RELEASE], header[RPM.EPOCH]))

        package_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                header[RPM.RELEASE], header[RPM.EPOCH])

        assert package_id

        return package_id
                
    def _getRpmId(self, path):
        self.cursor.execute('''select rpm_id from RPM
                        where pathname = %s''', (path,))
        result = self.cursor.fetchall()
        assert (len(result) <= 1)
        if (len(result) == 0):
            return None
        else:
            return int(result[0][0])


    def _getSrpmId(self, filename):
        self.cursor.execute('''select srpm_id from SRPM
                            where filename = %s''', (filename,))
        result = self.cursor.fetchall()
        if (len(result) == 0) :
            return None
        else:
            return int(result[0][0])


    def _insertRpmTable(self, header, package_id, ch_id):
        rpm_id = self._getRpmId(header[RPM.CT_PATHNAME])
        srpm_id = self._getSrpmId(header[RPM.SOURCERPM]) or 0

        if not rpm_id:
            self.cursor.execute('''insert into RPM
                                (package_id, srpm_id, pathname, arch, size)
                                values
                                (%d, %d, %s, %s, %s)''',
                                (package_id, srpm_id, header[RPM.CT_PATHNAME],
                                 header[RPM.ARCH], header[RPM.CT_FILESIZE]))

        rpm_id = self._getRpmId(header[RPM.CT_PATHNAME])
        assert rpm_id
        # We'll need to update the provides and obsoletes tables here...

        self._insertObsoletes(rpm_id, header)
        self._insertProvides(rpm_id, header)

        return rpm_id

    def _insertObsoletes(self, rpm_id, header):
        for obs in header[RPM.CT_OBSOLETES]:
            self.cursor.execute('''insert into RPMOBSOLETE
                            (rpm_id, name, vers, flags)
                            values
                            (%d, %s, %s, %s)''', 
                            (rpm_id, obs[0], obs[1], obs[2]))
 
    def _insertProvides(self, rpm_id, header):
        for prov in header[RPM.CT_PROVIDES]:
            self.cursor.execute('''insert into RPMPROVIDE
                            (rpm_id, name, vers, flags)
                            values
                            (%d, %s, %s, %s)''', 
                            (rpm_id, prov[0], prov[1], prov[2]))

        # We also "provide" all the "files"- should this be a separate table?
        # I'm answering "no" provisionally to avoid a schema update.
        plst = ()
        for prov in header[RPM.FILENAMES]:
            self.cursor.execute('''insert into RPMPAYLOAD
                            (rpm_id, name)
                            values
                            (%d, %s)''', (rpm_id, prov))


    def _scanForFiles(self, channel):
        result = 1
        self.cursor.execute('''select pathname from RPM
                inner join CHAN_RPM_ORIG on (RPM.rpm_id = CHAN_RPM_ORIG.rpm_id)
                inner join CHANNEL on (CHANNEL.channel_id = CHAN_RPM_ORIG.chan_id)
                where (CHANNEL.label = %s)''', (channel,))
        query = self.cursor.fetchall()
        for row in query:
            filename = row[0]
            result = result and os.access(filename, os.R_OK)
        return result

    def _setActiveElems(self, channel):
        # This is what sets which RPMS are active.  I'tll be fun to diagnose...
        self.cursor = self.conn.cursor()
        # Ok, zeroth, clear out the existing active RPMS
        # I know this can be optimized.  Work with me.
        self.cursor.execute('''select channel_id from CHANNEL
                            where label = %s''', (channel,))
        res = self.cursor.fetchall()
        assert (len(res) == 1)
        chan_id = int(res[0][0])
        self.cursor.execute('''delete from CHAN_RPM_ACT 
                            where chan_id = %d''', (chan_id,))

        # First, get a list of unique pkg names:

        self.cursor.execute('''select distinct pkgname from PACKAGE
                    inner join RPM on (PACKAGE.package_id = RPM.package_id)
                    inner join CHAN_RPM_ORIG on (RPM.rpm_id = CHAN_RPM_ORIG.rpm_id)
                    inner join CHANNEL on (CHANNEL.channel_id = CHAN_RPM_ORIG.chan_id)
                    where CHANNEL.label = %s''', (channel,))
        pkgs = []
        newest_ids = []
        query = self.cursor.fetchall()
        for row in query:
            pkgs.append(row[0])

        for pkg in pkgs:
            for id in self._findNewest(channel, pkg):
                newest_ids.append(id)

        self.cursor = self.conn.cursor()
        for id in newest_ids:
            log('setting rpmid %s active' % id)
            self.cursor.execute('''insert into CHAN_RPM_ACT
                                (rpm_id, chan_id)
                                values
                                (%d, %d)''', (id, chan_id))

        self.conn.commit()
        return "done"

    def _findNewest(self, channel, pkg):
        self.cursor.execute('''select pkgname, version, release, epoch from PACKAGE
                    inner join RPM on (PACKAGE.package_id = RPM.package_id)
                    inner join CHAN_RPM_ORIG on (CHAN_RPM_ORIG.rpm_id = RPM.rpm_id)
                    inner join CHANNEL on (CHAN_RPM_ORIG.chan_id = CHANNEL.channel_id)
                    where PACKAGE.pkgname = %s and CHANNEL.label = %s''',
                    (pkg, channel))
        query = self.cursor.fetchall()

        # Sort the list
        # We construct the lambda backwards so that it's actually sorted in 
        # reverse order...
        # FIXME: why does this try block need to be here?
        try:
            query = list(query)
        except:
            pass
        query.sort(lambda x,y: RPM.versionCompare((y[3], y[1], y[2]), (x[3], x[1], x[2])))

        # Now update the RPM table appropriately.
        self.cursor.execute('''select RPM.rpm_id from RPM
                    inner join PACKAGE on (PACKAGE.package_id = RPM.package_id)
                    inner join CHAN_RPM_ORIG on (RPM.rpm_id = CHAN_RPM_ORIG.rpm_id)
                    inner join CHANNEL on (CHAN_RPM_ORIG.chan_id = CHANNEL.channel_id)
                    where PACKAGE.pkgname = %s
                        and PACKAGE.version = %s
                        and PACKAGE.release = %s
                        and PACKAGE.epoch = %s 
                        and CHANNEL.label = %s''',
                    (query[0][0], query[0][1], query[0][2], query[0][3], channel))
        queryret = self.cursor.fetchall()
        retval = []
        for row in queryret:
            retval.append(row[0])
        return retval


    def _populateChannelDirs(self, config, channel):
        logfunc(locals(), DEBUG2)
        results = {}
        self.cursor.execute('''select lastupdate from CHANNEL where
                    CHANNEL.label = %s''', (channel,))
        qry = self.cursor.fetchall()
        # Should only be one channel...
        assert (len(qry) == 1)
        updatefilename = qry[0][0]

        # First, populate the listPackages directory.
        log("Grabbing listPackages information", TRIVIA)
        self.cursor.execute('''select PACKAGE.pkgname, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch, RPM.size, CHANNEL.label from
                PACKAGE, RPM
                inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                inner join CHANNEL on (CHAN_RPM_ACT.chan_id = CHANNEL.channel_id)
                where CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                order by PACKAGE.pkgname''', (channel,))
        query = self.cursor.fetchall()
        try:
            query = list(query)
        except:
            pass
        query = (query,)
        log("Creating listPackages file", DEBUG2)
        pathname = os.path.join(config['current_dir'], 'www', channel, 'listPackages', updatefilename)
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
        self.cursor.execute('''select PACKAGE.pkgname, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch,
                RPMOBSOLETE.name, RPMOBSOLETE.vers, RPMOBSOLETE.flags
                from PACKAGE, RPMOBSOLETE, RPM
                inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                inner join CHANNEL on (CHAN_RPM_ACT.chan_id = CHANNEL.channel_id)
                where CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                and RPM.rpm_id = RPMOBSOLETE.rpm_id 
                order by PACKAGE.pkgname''', (channel,))
        query = self.cursor.fetchall()
        for row in query:
            for item in row:
                if (item == None):
                    item = ''
                if (type(item) != type('')):
                    item = str(item)
        query = (query,)
        log("Creating getObsoletes file", DEBUG2)
        pathname = os.path.join(config['current_dir'], 'www', channel, 'getObsoletes', updatefilename)
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
        # FIXME: why is SRPM.filename listed twice here???
        self.cursor.execute('''select distinct SRPM.filename, SRPM.pathname from SRPM
                inner join RPM on (SRPM.srpm_id = RPM.srpm_id)
                inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                inner join CHANNEL on (CHAN_RPM_ACT.chan_id = CHANNEL .channel_id)
                where CHANNEL.label = %s''', (channel,))
        query = self.cursor.fetchall()
        dpath = os.path.join(config['current_dir'], 'www', channel, 'getPackageSource')
        log("Unlinking old files...", TRIVIA)
        for file in os.listdir(dpath):
            os.unlink(os.path.join(dpath, file))
        log("Creating symlinks...", DEBUG2)
        for row in query:
            src = row[1]
            dst = os.path.join(dpath, row[0])
            os.symlink(src, dst)
        log("getPackageSource synlinks created", DEBUG)
        results['getPackageSource'] = "ok"

        # now populate getPackage
        log("grabbing getPackage information", TRIVIA)
        self.cursor.execute('''select RPM.pathname from RPM
                    inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                    inner join CHANNEL on (CHAN_RPM_ACT.chan_id = CHANNEL.channel_id)
                    where CHANNEL.label = %s''', (channel,))
        query = self.cursor.fetchall()
        dpath = os.path.join (config['current_dir'], 'www', channel, 'getPackage')
        log("Unlinking old files...", TRIVIA)
        for file in os.listdir(dpath):
            os.unlink(os.path.join (dpath, file))
        log("Creating getPackage symlinks...", DEBUG2)
        for row in query:
            dir = os.path.join(dpath, os.path.basename(row[0]))
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

        log("arch: %s, rel: %s" % (carch, release))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''select name, label, arch, description, 
                    lastupdate from CHANNEL
                    where arch = %s
                    and osrelease = %s''', (carch, release))
        query = self.cursor.fetchall()
        log("found: %s" % str(query))
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
        self.cursor.execute('''select channel_id from CHANNEL
                where label = %s''', (label,))
        channels = self.cursor.fetchall()
        if (len(channels) != 1):
            log("crap...  no active channels found in solveDependencies...", DEBUG2)
            return None 
        act_ch_id = channels[0][0]
        # Find the RPM ID of the package in the active channel
        self.cursor.execute('''select distinct  
                    RPMPROVIDE.rpm_id from RPMPROVIDE
                    inner join RPM on (RPMPROVIDE.rpm_id = RPM.rpm_id)
                    inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                    where CHAN_RPM_ACT.chan_id = %s
                    and name = %s''', (act_ch_id, unknown))
        rpms = self.cursor.fetchall()
        if (len(rpms) == 0):
            log("Could not find active RPM solving for unknown %s" % (unknown), DEBUG2)
            return None
        if (len(rpms) > 1):
            log('More than one possible solution for dep %s - potential problem.' % (unknown,))
        # Just take the first one, in case there's more than one.
        id = rpms[0][0]

        # Grab the active package
        self.cursor.execute('''select p.pkgname, p.version, p.release,
                p.epoch, r.arch, r.size
                from PACKAGE as p, RPM as r
                where p.package_id = r.package_id
                and r.rpm_id = %s''', (id,))
        result = self.cursor.fetchall()
        if (len(result) != 1):
            log('Crap.  %d results returned.' % (len(results),))
            return None
        logfunc(locals())
        log("up2date.solveDependency is returning %s" % result, DEBUG)
        if (type(result[0]) != type([])):
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
        self.cursor.execute('''select lastupdate from CHANNEL
                    where arch = %s
                    and osrelease = %s
                    order by lastupdate desc''', (carch, release))
        result = self.cursor.fetchall()
        self.conn.commit()
        if (len(result) < 1):
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
        self.cursor.execute(''' select pkgname, version, release, epoch
                from PACKAGE
                inner join RPM on (RPM.package_id = PACKAGE.package_id)
                inner join CHAN_RPM_ACT on (RPM.rpm_id = CHAN_RPM_ACT.rpm_id)
                inner join CHANNEL on (CHANNEL.channel_id = CHAN_RPM_ACT.chan_id)
                where CHANNEL.arch = %s and CHANNEL.osrelease = %s
                order by pkgname''', (arch, release))
        result = self.cursor.fetchall()
        log('grabbed %s packages' % len(result))
        return result


