""" Implementation of the PostgreSQL backend for Current"""

import gzip
import os
import os.path
import pprint
import string 
import sys
import time

import pgdb
import xmlrpclib

from db.currentdb import CurrentDB
from logger import *
import archtab
import RPM
import schema

class PostgresDB(CurrentDB):
    def __init__(self, config):
        self.conn = None
        self.cursor = None

        # Copy in the config information - we need it to connect, and we 
        # need it when creating and updating channels.
        self.config = config
        

    def __del__(self):
        self.disconnect()


    def connect(self):
        log("Obtaining connection", TRACE)
        if self.conn:
            log("Connection already exists!", TRACE)
            return
        try:
            self.conn = pgdb.connect(user=self.config['db_user'], 
                                     password=self.config['db_pass'], 
                                     host=self.config['db_host'], 
                                     database=self.config['db_name'])
            log("Connected via user/password", TRACE)
        except Exception, e:
            log("No connection obtained!", TRACE)
            # FIXME: Not valid to call sys.exit() from mod_python
            sys.exit(0)
        
        # Also get a cursor 
        self.cursor = self.conn.cursor()


    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None


    ## API FUNCTIONS BELOW THIS POINT ##

    def initdb(self):
        self.connect()
        self.cursor.execute(schema.INITDB)
        self.conn.commit()
        log("Database table create commited.  Initdb done.", TRACE)


    def makeChannel(self, channel):
        logfunc(locals(), TRACE)

        # FIXME: Need to check for duplicate channel creation.
        # Labels must be unique, everything else can be duplicated.
        # We get compatible (as opposed to parent / child) channels for free
        # from this scheme...  cool.

        if (channel.has_key('parent')):
            log("Creating a child channel", TRACE)
            # First, grab some of the information from the parent
            self.cursor.execute('''select channel_id, arch, osrelease
                                   from CHANNEL 
                                   where label = %s''', 
                                (channel['parent'],))
            (parentchannel_id, arch, osrelease = self.cursor.fetchone()
        else:
            parentchannel_id = None
            arch = channel['arch']
            osrelease = channel['release']

        self.cursor.execute('''insert into CHANNEL
                               (name, label, arch, osrelease, description, 
                               lastupdate, parentchannel_id)
                               values (%s, %s, %s, %s, %s, %s, %s)''', 
                            (channel['name'],
                             channel['label'],
                             arch,
                             rel,
                             channel['desc'],
                             None,    # we haven't done our first update ...
                             parentchannel_id))
        self.conn.commit()
        log("New channel created and committed.", TRIVIA)

        # Now create the directories on disk for this channel
        webdir = os.path.join(self.config['current_dir'], 'www')
        chan_dir = os.path.join(webdir, channel['label'])
        if (not os.access(chan_dir, os.W_OK)):
            os.mkdir(chan_dir)
            for dir in ['getObsoletes', 'getPackage', 'getPackageHeader',
                        'getPackageSource', 'listPackages']:
                os.mkdir(os.path.join(chan_dir, dir))
        # FIXME: need an else here for error handling

        log("New channel and dirs created.", DEBUG2)

        return "ok"


    def addDir(self, label, dirname):
        logfunc(locals(), TRACE)

        self.cursor.execute('''select channel_id 
                               from CHANNEL 
                               where label = %s''',
                            (label,))
        channel_id  = self.cursor.fetchone()[0]

        # FIXME: doesn't check for duplicates.
        self.cursor.execute('''insert into CHANNEL_DIR 
                               (channel_id, dirpathname) 
                               values (%d, %s)''', 
                            (channel_id, dirname))
        self.conn.commit()
        log("Directory added to channel", DEBUG2)
        return "ok"


    def updateChannel(self, channel):
        # This would be a good place to drop the indexes...  then recreate them
        # when we're all done.  We don't do that yet.
        # FIXME: and we can't, if we're going to stay online while we update
        logfunc(locals(), TRACE)
        result = {}

        # scan the filesystem, see if anything changed
        (added_rpms, deleted_rpms) = self._scanFilesystem(channel)
        
        # Delete or add first?
        result['deleterpms'] = self._deleteRpms(channel, deleted_rpms)
        result['addrpms'] = self._addRpms(channel, added_rpms)

        if we_did_something:
            result['setactive'] = self._setActiveElems(channel)

            result['populatedirs'] = self._populateChannelDirs(channel)

            self._updateChannelTimeStamp(channel)

        return result


    def _scanFilesystem(self, channel):

        # Helper function for actually scanning the files on disk
        def filesystemWalker(fs_set, dirname, filenames):
            for filename in filenames:
                fs_set.add(os.path.join(dirname, filename))

        # Get the set of all rpms/files in the filesystem
        self.cursor.execute('''select dirpathname
                               from CHANNEL, DIR, CHANNEL_DIR
                               where CHANNEL.channel_id = CHANNEL_DIR.channel_id and
                                     CHANNEL_DIR.dir_id = DIR.dir_id and 
                                     CHANNEL.label = %s''',
                            (channel,))
        query = self.cursor.fetchall()

        fs_set = sets.Set()
        for row in query:
            os.path.walk(row[0], filesystemWalker, fs)

        # Get the set of all the rpm pathnames in the database
        self.cursor.execute('''select pathname
                               from CHANNEL, CHANNEL_RPM
                               where CHANNEL.channel_id = CHANNEL_RPM.channel_id and
                               CHANNEL.label = %s''',
                            (channel,))
        query = self.cursor.fetchall() # FIXME: 256 at a time??
        db_set = sets.Set()
        for row in query:
            db_set.add(row[0])

        # Now see what was added or deleted, if anything 
        added_set = fs_set.difference(db_set)
        deleted_set = db_set.difference(fs_set)

        return (added_set, deleted_set)


    def _deleteRpms(self, channel, delete_set):
        """ Given a set of full pathnames, delete them from the channel.

        Note that the FILES are gone - we know what the full pathnames used
        to be because they were recorded in the database.
    
        """

        # the full pathname is in CHANNEL_RPM.
        # grab the rpm_id from that row 
        # delete that item
        # if thats the last row in CHANNEL_RPM with that rpm_id,
        # delete that rpm_id from RPM
        #     if thats the last row in RPM with that package_id
        #        delete that package_id from PACKAGE
        # delete that rpm_id from all the other tables with rpm_id
        # Then do the disk cleanup. See what _addRpms puts down...
        pass


    def _addRpms(self, channel, add_set):
        """ Given a set of full pathnames, add them to a channel. """

        pass

        
    def _addRpmPackage(self, path, channel):
        filename = os.path.basename(path)
        header = RPM.Header(path)
        
        if (header.hdr == None):
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
        dirname = os.path.join(self.config['current_dir'], 'www', channel, 'getPackageHeader')
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


    def _insertPackageTable(self, header):
        package_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                        header[RPM.RELEASE], header[RPM.EPOCH])

        if not package_id:
            self.cursor.execute('''insert into PACKAGE
                        (pkgname, version, release, epoch)
                        values (%s, %s, %s, %s)''',
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


    def _setActiveChannelRpms(self, channel):
        # This is what sets which RPMS are active.  I'tll be fun to diagnose...
        # clear out the existing active RPMS
        # FIXME: Can this be optimized any?
        # Would version compare in PL/SQL do us any good?

        # Clear out this channels entries from the CHANNEL_RPM_ACTIVE table
        self.cursor.execute('''select channel_id from CHANNEL
                               where label = %s''', (channel,))
        result = self.cursor.fetchone()
        chan_id = result[0]
        self.cursor.execute('''delete from CHANNEL_RPM_ACTIVE
                               where chan_id = %d''', (chan_id,))

        # First, get a list of unique pkg names:
        self.cursor.execute('''select distinct name 
                               from PACKAGE, RPM, CHANNEL_RPM
                               where PACKAGE.package_id = RPM.package_id and
                                     RPM.rpm_id = CHAN_RPM_ORIG.rpm_id and 
                                     CHANNEL.channel_id = CHAN_RPM_ORIG.chan_id and 
                                     CHANNEL.label = %s''', (channel,))
        newest_ids = []
        query = self.cursor.fetchall()
        for row in query:
            for id in self._findNewest(channel, row[0]):
                newest_ids.append(id)

        for id in newest_ids:
            log('setting rpmid %s active' % id)
            self.cursor.execute('''insert into CHANNEL_RPM_ACTIVE
                                   (rpm_id, chan_id)
                                   values (%d, %d)''', (id, chan_id))

        self.conn.commit()
        return "done"


    def _findNewest(self, channel, pkg):
        self.cursor.execute('''select PACKAGE.name, PACKAGE.version, PACKAGE.release, PACKAGE.epoch 
                               from PACKAGE, RPM, CHANNEL_RPM, CHANNEL
                               where PACKAGE.package_id = RPM.package_id and
                                     RPM.rpm_id = CHANNEL_RPM.rpm_id and 
                                     CHANNEL_RPM.chan_id = CHANNEL.channel_id and
                                     PACKAGE.name = %s and 
                                     CHANNEL.label = %s''', (pkg, channel))
        query = self.cursor.fetchall()

        # Sort the list according to RPM.versionCompare() results
        # We construct the lambda backwards so that it's actually sorted in 
        # reverse order...
        # BUG: The list() used to be in a try/except block - WHY?
        query = list(query)
        query.sort(lambda x,y: RPM.versionCompare((y[3], y[1], y[2]), (x[3], x[1], x[2])))

        # From the first of that reverse list, grab the RPM.rpm_id of the _NEWEST_ rpm available
        self.cursor.execute('''select RPM.rpm_id 
                               from RPM, PACKAGE, CHANNEL_RPM, CHANNEL
                               where PACKAGE.package_id = RPM.package_id and 
                                     RPM.rpm_id = CHANNEL_RPM.rpm_id and 
                                     CHANNEL_RPM.chan_id = CHANNEL.channel_id and 
                                     PACKAGE.pkgname = %s and 
                                     PACKAGE.version = %s and 
                                     PACKAGE.release = %s and 
                                     PACKAGE.epoch = %s  and 
                                     CHANNEL.label = %s''',
                    (query[0][0], query[0][1], query[0][2], query[0][3], channel))

        # We really are going to get a list here on occasion - 
        # we'll get the i386, i486, etc varients of the kernel package of the newest version
        query = self.cursor.fetchall()
        tmp = []
        for row in query:
            tmp.append(row[0])
        return tmp


    def _populateChannelDirs(self, channel):
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
        pathname = os.path.join(self.config['current_dir'], 'www', channel, 'listPackages', updatefilename)
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
        pathname = os.path.join(self.config['current_dir'], 'www', channel, 'getObsoletes', updatefilename)
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
        dpath = os.path.join(self.config['current_dir'], 'www', channel, 'getPackageSource')
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
        dpath = os.path.join (self.config['current_dir'], 'www', channel, 'getPackage')
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


