""" A single "virtual" interface for all the storage needs.

The api modules (up2date, errata, etc) make calls into the CurrentDB - the
api modules have no knowledge of the storage method itself. Conversely,
CurrentDB knows nothing of xmlrpc, GET methods, or other delusions.

Copyright (c) 2002, 2004 Hunter Matthews, Jack Neely    

Distributed under GPL.

"""

import os
import os.path
import pprint
import string 
import sys
import time

from db.resultSet import resultSet
from logger import *
import exception
import archtab
import RPM
import sets
import xmlrpc

# Constants used in data base schema
PROVIDES  = 0
OBSOLETES = 1
FILES     = 2

class specificDB(object):
    """An Abstract class.  For each database we whish to support that
       module needs to provide an object that inherits from this base
       class.  This base class contains all the database specific
       code."""

    def __init__(self, config):
        pass

    def getConnection(self):
        raise exception.CurrentDB(
                "You cannot use the specificDB abstract class")

    def getCursor(self):
        return None

    def initdb(self):
        pass



class CurrentDB(object):
    
    def __init__(self, config, specific):
        # Copy in the config information - we need it to connect, and we 
        # need it when creating and updating channels.
        self.config = config
        self.specific = specific

        self.conn = self.specific.getConnection()
        self.cursor = self.specific.getCursor()
        

    def initdb(self):
        "Init the database."

        # Pass on to the specific layer
        self.specific.initdb()

        
    def abort(self):
        """If an exception occures in a cirtical part of the DB code
           we need to be able to abore the transaction."""

        self.conn.rollback()


    def makeChannel(self, channel):
        logfunc(locals(), TRACE)

        # FIXME: Need to check for duplicate channel creation.
        # Labels must be unique, everything else can be duplicated.
        # We get compatible (as opposed to parent / child) channels for free
        # from this scheme...  cool.

        if (channel.has_key('parent')):
            log("Creating a child channel", DEBUG)
            # First, grab some of the information from the parent
            self.cursor.execute('''select channel_id, arch, osrelease
                                   from CHANNEL 
                                   where label = %s''', 
                                (channel['parent'],))
            (parentchannel_id, arch, osrelease) = self.cursor.fetchone()
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
                             osrelease,
                             channel['desc'],
                             None,    # we haven't done our first update ...
                             parentchannel_id))
        self.conn.commit()
        log("New channel created and committed.", DEBUG)

        # Now create the directories on disk for this channel
        webdir = os.path.join(self.config['current_dir'], 'www')
        chan_dir = os.path.join(webdir, channel['label'])
        if not os.access(chan_dir, os.W_OK):
            os.mkdir(chan_dir)
            for dir in ['getObsoletes', 'getPackage', 'getPackageHeader',
                        'getPackageSource', 'listPackages']:
                os.mkdir(os.path.join(chan_dir, dir))
        # FIXME: need an else here for error handling

        log("New channel and dirs created.", DEBUG)

        return 0


    def addDir(self, label, dirname):
        # check for existing added dirs?
        logfunc(locals(), TRACE)

        channel_id  = self._getChanID(label)
        if not channel_id:
            raise exception.CurrentDB("Bad channel label.")

        # FIXME: doesn't check for duplicates.
        self.cursor.execute('''insert into CHANNEL_DIR 
                               (channel_id, dirpathname) 
                               values (%d, %s)''', 
                            (channel_id, dirname))
        self.conn.commit()
        log("Directory added to channel", DEBUG)
        return 0


    def updateChannel(self, channel):
        logfunc(locals(), TRACE)
        result = {}

        # scan the filesystem, see if anything changed
        (added_rpms, deleted_rpms) = self._scanFilesystem(channel)
        
        # Delete or add first?
        result['deletedrpms'] = self._deleteRpms(channel, deleted_rpms)
        result['addedrpms'] = self._addRpms(channel, added_rpms)

        if len(added_rpms) + len(deleted_rpms) > 0:
            # Only want to run if we actually added or removed packages
            self._updateChannelTimeStamp(channel)

            result['setactive'] = self._setActiveChannelRpms(channel)

            result['populatedirs'] = self._populateChannelDirs(channel)

            # Run setActive and populateChannel on any channels
            # which may now be stale.  Other channels may include
            # RPMs that were removed.
            staleChans = result['deletedrpms']['staleChans']
            for chan in staleChans:
                log("Running setActiveChannelsRrpms and populateChannelDirs "
                    "on channel %s." % chan, DEBUG)
                self._updateChannelTimeStamp(chan)
                retActive = self._setActiveChannelRpms(chan)
                retPop = self._populateChannelDirs(chan)
                result[chan+"_setactive"] = retActive
                result[chan+"_populatedirs"] = retPop
                

        self.conn.commit()

        return result


    def _updateChannelTimeStamp(self, channel):
        """Update the channel's time stamp for right now."""

        # Format: YYYYMMDDHHMMSS
        t = time.strftime("%Y%m%d%H%M%S")
        chanID = self._getChanID(channel)

        self.cursor.execute("""update CHANNEL set lastupdate = %s
                            where channel_id = %d""", (t, chanID))

        return 0


    def _scanFilesystem(self, channel):

        # Helper function for actually scanning the files on disk
        def filesystemWalker(fs_set, dirname, filenames):
            for filename in filenames:
                if filename[-4:] == '.rpm':
                    path = os.path.join(dirname, filename)
                    if os.access(path, os.R_OK):
                        fs_set.add(path)
                    else:
                        raise exception.CurrentDB("Cannot read %s" % filename)

        # Get the set of all rpms/files in the filesystem
        self.cursor.execute('''select dirpathname
                    from CHANNEL, CHANNEL_DIR
                    where CHANNEL.channel_id = CHANNEL_DIR.channel_id and
                    CHANNEL.label = %s''',
                    (channel,))
        query = self.cursor.fetchall() 

        fs_set = sets.Set()
        for row in query:
            os.path.walk(row[0], filesystemWalker, fs_set)

        # Get the set of all the rpm pathnames in the database
        self.cursor.execute('''select filename
                               from RPM, CHANNEL, CHANNEL_RPM
                               where CHANNEL.channel_id = CHANNEL_RPM.channel_id
                               and CHANNEL_RPM.rpm_id = RPM.rpm_id
                               and CHANNEL.label = %s''',
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

        staleChans = []
        c = 0

        for file in delete_set:
            log("Removing: %s" % file, DEBUG2)
            self.cursor.execute("""select rpm_id, package_id from RPM
                                   where filename = %s""", (file,))
            r = resultSet(self.cursor)
            rpm_id = r['rpm_id']
            package_id = r['package_id']

            self.cursor.execute("""delete from RPM where rpm_id = %s""",
                                (rpm_id,))
            self.cursor.execute("""delete from DEPENDANCIES 
                                   where rpm_id = %s""",
                                (rpm_id,))
            
            self.cursor.execute("""select count(*) from RPM where
                                   package_id = %s""", (package_id))
            r = resultSet(self.cursor)
            if r['count(*)'] == 0:
                # We know there are no more refferences to this PACKAGE
                self.cursor.execute("""delete from PACKAGE where 
                                       package_id = %s""", (package_id,))
            
            # Now the fun part...detect possibly stale channels
            self.cursor.execute("""select distinct CHANNEL.label from 
                     CHANNEL, CHANNEL_RPM_ACTIVE where
                     CHANNEL.channel_id = CHANNEL_RPM_ACTIVE.channel_id
                     and CHANNEL_RPM_ACTIVE.rpm_id = %s""",
                     (rpm_id,))
            
            r = resultSet(self.cursor)
            for row in r:
                if row['label'] not in staleChans and row['label'] != channel:
                    staleChans.append(row['label'])
            log("staleChans = %s" % str(staleChans), DEBUG2)

            # Now hope populateChannel gets re-run on those
            self.cursor.execute("""delete from CHANNEL_RPM where rpm_id = %s""",
                                (rpm_id,))
            self.cursor.execute("""delete from CHANNEL_RPM_ACTIVE 
                                   where rpm_id = %s""",
                                (rpm_id,))
            
            c = c + 1
        
        result = {}
        result['removedRPMS'] = c
        result['staleChans'] = staleChans
        
        return result


    def _addRpms(self, channel, add_set):
        """ Given a set of full pathnames, add them to a channel. """

        logfunc(locals(), TRACE)

        chanID = self._getChanID(channel)
        c = 0

        for rpm in add_set:
            log("Adding %s to channel %s" % (rpm, channel), TRIVIA)
            rpm_id = self._getRpmId(rpm)
            header = RPM.Header(rpm)
            
            if not rpm_id:
                # Need to load RPM info
                pkg_id = self._insertPackageTable(header)
                rpm_id = self._insertRpmTable(header, pkg_id, chanID)

                self._insertProvides(rpm_id, header)
                self._insertObsoletes(rpm_id, header)
            
            self._insertChannelTable(chanID, rpm_id)
            self._createHeader(channel, header)

            c = c + 1

        return c
    

    def _getChanID(self, channel):
        """Take a channel label and return the chan id from the DB."""

        self.cursor.execute("""select channel_id from CHANNEL
            where label = %s""", (channel,))

        r = resultSet(self.cursor)

        if r.rowcount() == 0:
            log("Tried to get channel ID for %s which doesn't exist" % channel,
                VERBOSE)
            return None
        
        return r['channel_id']

        
    def _insertChannelTable(self, chanID, rpmID):

        self.cursor.execute('''insert into CHANNEL_RPM (rpm_id, channel_id) 
                            values (%d, %d) ''', 
                            (rpmID, chanID))

        log("RPM ID=%s added to channel" % rpmID, TRACE)

        # Error checking?
        return 0


    def _createHeader(self, channelLabel, header):
        log("Inside _createHeader", TRACE)

        # XXX: do we do this more than once?  I think so
        dirname = os.path.join(self.config['current_dir'], 'www', 
                channelLabel, 'getPackageHeader')
        header.unload(dirname)

        # Error checking?
        return 0


    def _getPackageId(self, name, version, release, epoch, issource):
        #logfunc(locals(), TRACE)
        self.cursor.execute(''' select package_id from PACKAGE
                where name = %s
                and version = %s
                and release = %s
                and epoch = %s
                and issource = %s''', (name, version, release, 
                                       epoch, str(issource)))

        r = resultSet(self.cursor)
        try:
            return r['package_id']
        except IndexError, e:
            # No results returned
            return None


    def _insertPackageTable(self, header):
        package_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                        header[RPM.RELEASE], header[RPM.EPOCH],
                                        header[RPM.SOURCEPACKAGE])

        if not package_id:
            self.cursor.execute('''insert into PACKAGE
                        (name, version, release, epoch, issource)
                        values (%s, %s, %s, %s, %s)''',
                        (header[RPM.NAME], header[RPM.VERSION],
                         header[RPM.RELEASE], header[RPM.EPOCH],
                         header[RPM.SOURCEPACKAGE]))

        package_id = self._getPackageId(header[RPM.NAME], header[RPM.VERSION],
                                header[RPM.RELEASE], header[RPM.EPOCH],
                                header[RPM.SOURCEPACKAGE])
        if not package_id:
            log("Inserted package but could not lookup package_id", VERBOSE)
            
        return package_id

                
    def _getRpmId(self, path):
        self.cursor.execute('''select rpm_id from RPM
                        where filename = %s''', (path,))
        result = self.cursor.fetchall()
        if (len(result) == 0):
            return None
        else:
            return int(result[0][0])


    def _insertRpmTable(self, header, package_id, ch_id):
        rpm_id = self._getRpmId(header[RPM.CT_PATHNAME])
        if rpm_id:
            # RPM Already in DB
            return rpm_id
        
        self.cursor.execute('''insert into RPM
                               (package_id, filename, arch, size)
                               values
                               (%d, %s, %s, %s)''',
                            (package_id, header[RPM.CT_PATHNAME],
                             header[RPM.ARCH], header[RPM.CT_FILESIZE]))

        rpm_id = self._getRpmId(header[RPM.CT_PATHNAME])
        if not rpm_id:
            log("Inserted RPM but could not lookup rpm_id.", VERBOSE)
            return None

        return rpm_id


    def _setDependancy(self, dep, rpm_id, type, flags = None, vers = None):
        if flags != None and vers != None:
            query = """insert into DEPENDANCIES 
                       (rpm_id, dep, vers, flags, type) values
                       (%d, %s, %s, %s, %d)"""
            t = (rpm_id, dep, vers, flags, type)
        else:
            query = """insert into DEPENDANCIES (rpm_id, dep, type)
                       values (%d, %s, %d)"""
            t = (rpm_id, dep, type)

        self.cursor.execute(query, t)

        
    def _insertObsoletes(self, rpm_id, header):
        for obs in header[RPM.CT_OBSOLETES]:
            self._setDependancy(obs[0], rpm_id, OBSOLETES,
                                obs[2], obs[1])
 

    def _insertProvides(self, rpm_id, header):
        for prov in header[RPM.CT_PROVIDES]:
            self._setDependancy(prov[0], rpm_id, PROVIDES, 
                                prov[2], prov[1])
                
        # We also "provide" all the "files"
        for prov in header[RPM.FILENAMES]:
            self._setDependancy(prov, rpm_id, FILES)


    def _setActiveChannelRpms(self, channel):
        # This is what sets which RPMS are active.  I'tll be fun to diagnose...
        # clear out the existing active RPMS
        # FIXME: Can this be optimized any?
        # Would version compare in PL/SQL do us any good?

        # Clear out this channels entries from the CHANNEL_RPM_ACTIVE table
        chan_id = self._getChanID(channel)
        self.cursor.execute('''delete from CHANNEL_RPM_ACTIVE
                               where channel_id = %d''', (chan_id,))

        # First, get a list of unique pkg names:
        self.cursor.execute('''select distinct PACKAGE.name 
                               from PACKAGE, RPM, CHANNEL_RPM
                               where PACKAGE.package_id = RPM.package_id and
                                     RPM.rpm_id = CHANNEL_RPM.rpm_id and
                                     CHANNEL_RPM.channel_id = %d
                                     and PACKAGE.issource = 0''', (chan_id,))
        newest_ids = []
        query = self.cursor.fetchall()
        for row in query:
            for id in self._findNewest(chan_id, row[0]):
                newest_ids.append(id)

        for id in newest_ids:
            log('setting rpmid %s active' % id, DEBUG2)
            self.cursor.execute('''insert into CHANNEL_RPM_ACTIVE
                                   (rpm_id, channel_id)
                                   values (%d, %d)''', (id, chan_id))

        self.conn.commit()
        return 0


    def _findNewest(self, chanID, pkg):
        self.cursor.execute('''select PACKAGE.name, PACKAGE.version, 
                                      PACKAGE.release, PACKAGE.epoch 
                               from PACKAGE, RPM, CHANNEL_RPM
                               where PACKAGE.package_id = RPM.package_id and
                               RPM.rpm_id = CHANNEL_RPM.rpm_id and 
                               CHANNEL_RPM.channel_id = %d and
                               PACKAGE.issource = 0 and
                               PACKAGE.name = %s''', (chanID, pkg))
        query = self.cursor.fetchall()

        # Sort the list according to RPM.versionCompare() results
        # We construct the lambda backwards so that it's actually sorted in 
        # reverse order...
        # BUG: The list() used to be in a try/except block - WHY?
        query = list(query)
        query.sort(lambda x,y: RPM.versionCompare((y[3], y[1], y[2]), (x[3], x[1], x[2])))

        # From the first of that reverse list, grab the RPM.rpm_id 
        # of the _NEWEST_ rpm available
        # XXX: Why can't we do this in the above query?
        self.cursor.execute('''select RPM.rpm_id 
                               from RPM, PACKAGE, CHANNEL_RPM
                               where PACKAGE.package_id = RPM.package_id and 
                                     RPM.rpm_id = CHANNEL_RPM.rpm_id and 
                                     CHANNEL_RPM.channel_id = %d and 
                                     PACKAGE.name = %s and 
                                     PACKAGE.version = %s and 
                                     PACKAGE.release = %s and 
                                     PACKAGE.epoch = %s  and
                                     PACKAGE.issource = 0''',
                    (chanID, query[0][0], query[0][1], 
                     query[0][2], query[0][3]))

        # We really are going to get a list here on occasion - 
        # we'll get the i386, i486, etc varients of the kernel 
        # package of the newest version
        query = self.cursor.fetchall()
        tmp = []
        for row in query:
            tmp.append(row[0])
        return tmp


    def _doListPackages(self, channel, filename):
        """Return a list suitable for creating an XML data chuck for
           up2date of all active packages in this channel."""

        self.cursor.execute('''select PACKAGE.name, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch, 
                RPM.size, CHANNEL.label 
                from PACKAGE, RPM
                inner join CHANNEL_RPM_ACTIVE on (RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id)
                inner join CHANNEL on (CHANNEL_RPM_ACTIVE.channel_id = CHANNEL.channel_id)
                where CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                and PACKAGE.issource = 0
                order by PACKAGE.name''', (channel,))
       
        xmlrpc.fileDump(self.cursor, filename, gz=1)


    def _doObsoletesList(self, channel, filename):
        """Return a list suitable for xmlrpclib of obsoletes for 
           this channel."""

        self.cursor.execute('''select PACKAGE.name, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch,
                DEPENDANCIES.dep, DEPENDANCIES.vers, DEPENDANCIES.flags
                from PACKAGE, DEPENDANCIES, RPM
                inner join CHANNEL_RPM_ACTIVE on (RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id)
                inner join CHANNEL on (CHANNEL_RPM_ACTIVE.channel_id = CHANNEL.channel_id)
                where CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                and RPM.rpm_id = DEPENDANCIES.rpm_id 
                and PACKAGE.issource = 0
                and DEPENDANCIES.type = %d
                order by PACKAGE.name''', (channel, OBSOLETES))
        
        xmlrpc.fileDump(self.cursor, filename, gz=1)


    def _getPackageSourceList(self, channel):
        """Blah, Blah, files for getPackageSource for this channel."""

        self.cursor.execute('''select RPM.filename from 
                RPM, PACKAGE, CHANNEL, CHANNEL_RPM
                where PACKAGE.issource = 1
                and CHANNEL.channel_id = CHANNEL_RPM.channel_id
                and CHANNEL_RPM.rpm_id = RPM.rpm_id
                and RPM.package_id = PACKAGE.package_id
                and CHANNEL.label = %s''', (channel,))
        query = self.cursor.fetchall()
        
        return query
   

    def _getPackageList(self, channel):
        """Blah, Blah, files for getPackage for this channel."""

        self.cursor.execute('''select RPM.filename from RPM
                    inner join CHANNEL_RPM_ACTIVE on (RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id)
                    inner join CHANNEL on (CHANNEL_RPM_ACTIVE.channel_id = CHANNEL.channel_id)
                    inner join PACKAGE on (RPM.package_id = PACKAGE.package_id)
                    where CHANNEL.label = %s
                    and PACKAGE.issource = 0''', (channel,))
        query = self.cursor.fetchall()
        
        return query

        
    def _populateChannelDirs(self, channel):
        logfunc(locals(), TRACE)
        results = {}

        self.cursor.execute('''select lastupdate from CHANNEL where
                    CHANNEL.label = %s''', (channel,))
        result = resultSet(self.cursor)
        updatefilename = result['lastupdate']
        if updatefilename == None:
            log("DB did not give us a lastupdate on channel %s" % channel,
                VERBOSE)
            return {"ERROR": "DB did not give us a lastupdate value"}

        # First, populate the listPackages directory.
        log("Creating listPackages information", DEBUG)
        pathname = os.path.join(self.config['current_dir'], 'www', 
                                channel, 'listPackages', updatefilename)
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        self._doListPackages(channel, pathname)
        log("listPackages file created successfully", TRIVIA)
        results['listPackages'] = "ok"
        
        # Now populate the getObsoletes directory.
        log("Creating getObsoletes file", DEBUG)
        pathname = os.path.join(self.config['current_dir'], 'www', 
                                channel, 'getObsoletes', updatefilename)
        if (os.path.exists(pathname)):
            os.unlink(pathname)
        self._doObsoletesList(channel, pathname)
        log("getObsoletes file created succefully", TRIVIA)
        results['getObsoletes'] = "ok"

        # Now populate getPackageSource
        log("grabbing getPackageSource information", TRIVIA)
        query = self._getPackageSourceList(channel)

        log("Creating getPacageSource symlinks", DEBUG)
        dpath = os.path.join(self.config['current_dir'], 'www', channel, 'getPackageSource')
        log("Unlinking old files...", TRIVIA)
        for file in os.listdir(dpath):
            os.unlink(os.path.join(dpath, file))
        log("Creating symlinks...", DEBUG2)
        for row in query:
            src = row[0]
            os.symlink(src, os.path.join(dpath, os.path.basename(src)))
        log("getPackageSource synlinks created successfully", DEBUG)
        results['getPackageSource'] = "ok"

        # now populate getPackage
        log("grabbing getPackage information", TRIVIA)
        query = self._getPackageList(channel)
        
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
                log("OS Error number %s occurred - why?" % error, MANDATORY)
                logException()
        log("getPackage symlinks created", DEBUG)
        results['getPackage'] = "ok"

        # getPackageHeader ought to already be populated, so we're done.
        return results


    def getCompatibleChannels(self, arch, release):
        # Need to return a dict with label and last modified of all compatible
        # channels (other information okay but not necessary)

        # get the canonical architecture.
        carch = archtab.getCannonArch(arch)

        log("arch: %s, rel: %s" % (carch, release), DEBUG2)
        self.cursor.execute('''select name, label, arch, description, 
                    lastupdate from CHANNEL
                    where arch = %s
                    and osrelease = %s''', (carch, release))
        query = self.cursor.fetchall()
        log("found: %s" % str(query), DEBUG2)
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
        logfunc(locals(), TRACE)
        act_ch_id = self._getChanID(label)
        
        # Find the RPM ID of the package in the active channel
        query =  '''select distinct  
                    DEPENDANCIES.rpm_id 
                    from DEPENDANCIES, RPM, CHANNEL_RPM_ACTIVE
                    where DEPENDANCIES.rpm_id = RPM.rpm_id
                    and RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id
                    and CHANNEL_RPM_ACTIVE.channel_id = %s
                    and DEPENDANCIES.type = %d
                    and DEPENDANCIES.dep = %s''' 
        self.cursor.execute(query, (act_ch_id, PROVIDES, unknown))
        r = resultSet(self.cursor)
        
        if (r.rowcount() == 0):
            # No PROVIDES satisfied the dependancy.  Look for files.
            self.cursor.execute(query, (act_ch_id, FILES, unknown))
            r = resultSet(self.cursor)
            if r.rowcount() == 0:
                log("Cound not resolve dependancy on %s" % unknown, DEBUG)
                return None
            
        if r.rowcount() > 1:
            log('More than one possible solution for dep %s' % 
                (unknown,), VERBOSE)
            
        # Just take the first one, in case there's more than one.
        id = r['rpm_id']

        # Grab the active package
        self.cursor.execute('''select p.name, p.version, p.release,
                p.epoch, r.arch, r.size
                from PACKAGE as p, RPM as r
                where p.package_id = r.package_id
                and r.rpm_id = %s''', (id,))
        result = self.cursor.fetchall()
        
        # Force list type as pysqlite uses a propriatary list/tuple type
        fixedResult = []
        for row in result:
            fixedResult.append(list(row))
        result = fixedResult

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
        result = resultSet(self.cursor)
        if (result.rowcount() != 1):
            log("No channel found in getLastUpdate with arch = %s and"
                " osrelease = %s" % (carch, release), VERBOSE)    
            raise exception.CurrentDB("No channel found in getLastUpdate")
        
        else:
            return result['lastupdate']


    def listAppletPackages(self, release, arch):
        # This routine will return a list of all packages in all compatible
        # channels - it's designed for use with the APPLET code.
        # FIXME: We will need to somehow determine which channels a given
        # client is subscribed to at a later point...  how to do this, if
        # uuid is unrelated to anything?  dunno...

        self.cursor.execute('''select PACKAGE.name, PACKAGE.version, 
                               PACKAGE.release, PACKAGE.epoch
                               from PACKAGE, RPM, CHANNEL_RPM_ACTIVE, CHANNEL
                               where
                               RPM.package_id = PACKAGE.package_id and
                               RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id and 
                        CHANNEL.channel_id = CHANNEL_RPM_ACTIVE.channel_id and
                        CHANNEL.arch = %s and CHANNEL.osrelease = %s
                        order by PACKAGE.name''', (arch, release))
        result = self.cursor.fetchall()
        log('grabbed %s packages in listAppletPackages' % len(result), DEBUG2)
        return result


