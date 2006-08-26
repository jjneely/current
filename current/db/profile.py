#!/usr/bin/python
#
# profile.py - Client profile interface
#
# Copyright 2005 Jack Neely <jjneely@gmail.com>
#
# SDG
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from current.exception import *
from current import db
from current.db.resultSet import resultSet
from current import RPM
from current.logger import *
from current.archtab import *

# Constants used in database schema
OLDIE     = 0
UP2DATE   = 1
EXTRA     = 2
UPDATABLE = 3
ORPHANED  = 4

class CurrentProfileDB(CurrentDB):
    pass

class ProfileDB(object):

    def __init__(self):
        self.conn   = db.sdb.getConnection()
        self.cursor = db.sdb.getCursor()

    def addProfile(self, user, arch, os_release, name, release_name, uuid):
        q = """insert into PROFILE (profile_id, user_id, architecture, 
               cannon_arch, os_release, name, release_name, uuid)
               values (NULL, %s, %s, %s, %s, %s, %s, %s)"""
               
        t = (user, arch, getCannonArch(arch), os_release, name, release_name, uuid)

        self.cursor.execute(q, t)
        self.conn.commit()

        return self.getProfileID(uuid)


    def getProfileID(self, uuid):
        q = "select profile_id from PROFILE where uuid = %s"
        self.cursor.execute(q, (uuid,))
        
        result = resultSet(self.cursor)
        if result.rowcount() == 0:
            return None
        
        return result['profile_id']
    
    def getProfile(self, id):
        q = """select user_id, architecture, os_release, name, release_name, uuid
               from PROFILE where profile_id = %s"""

        self.cursor.execute(q, (id,))
        r = self.cursor.fetchone()
        
        # if r is None that's what we want
        return r

    def delete(self, pid):
        "Remove a profile"

        qlist = [
            "delete from PROFILE where profile_id = %s",
            "delete from SUBSCRIPTIONS where profile_id = %s",
            "delete from INSTALLED where profile_id = %s",
            "delete from HARDWARE where profile_id = %s",
            ]

        for q in qlist:
            self.cursor.execute(q, (pid,))

        self.conn.commit()
       
    def setupBaseChannels(self, pid):
        """Subscribe profile to all matching base channels."""

        # XXX: Schema here isn't consistant
        # Do this completely in SQL?  What about duplicate subscriptions?
        q = """select CHANNEL.channel_id from CHANNEL, PROFILE where
               CHANNEL.base != 0 and
               PROFILE.profile_id = %s and
               PROFILE.cannon_arch = CHANNEL.arch and
               PROFILE.os_release = CHANNEL.osrelease"""

        self.cursor.execute(q, (pid,))
        result = resultSet(self.cursor)
        chans = []
        for row in result:
            chans.append(row['channel_id'])

        for c in chans:
            self.subscribe(pid, c)
        
    def getAuthorizedChannels(self, uuid):
        """Return a channel struct of the subscribed channels for this pid."""

        q = """select CHANNEL.name, CHANNEL.label, CHANNEL.arch, 
                 CHANNEL.description, CHANNEL.lastupdate, 
                 CHANNEL.parentchannel_id 
                 from CHANNEL, PROFILE, SUBSCRIPTIONS where
                 PROFILE.profile_id = SUBSCRIPTIONS.profile_id and
                 CHANNEL.channel_ID = SUBSCRIPTIONS.channel_id and
                 PROFILE.uuid = %s"""
        
        self.cursor.execute(q, (uuid,))
        chanList = resultSet(self.cursor).dump()
        for c in chanList:
            log("AuthorizedChannels: : %s" % str(c), DEBUG2)
            if c['parentchannel_id'] == None:
                c['parentchannel_id'] = ''

        return chanList

    def getChannels(self, pid):
        """Returns channel IDs of the channels this machine (pid) is
           subscribed to.  An empty set is returned for no channels."""

        q = "select channel_id from SUBSCRIPTIONS where profile_id = %s"
        self.cursor.execute(q, (pid,))

        result = resultSet(self.cursor)
        ret = []
        for row in result:
            ret.append(row['channel_id'])

        return ret

    def subscribe(self, pid, channel):
        """Subscribe a profile to a channel."""

	# PM2006: type(channel) == type(1) does not work. With mysql
        # as DB backend, type(channel) becomes long, and type(1) is int.
        if type(channel) == type('a'):
            q = """insert into SUBSCRIPTIONS (profile_id, channel_id)
                   select %s, channel_id from CHANNEL where label = %s"""
        else:
            q = """insert into SUBSCRIPTIONS (profile_id, channel_id) values
                   (%s, %s)"""

        self.cursor.execute(q, (pid, channel))
        self._updateInstalledPackages(pid)
        self.conn.commit()
        
    def unsubscribe(self, pid, channel):
        """Unsubscribe a profile from a channel."""

        q = """delete from SUBSCRIPTIONS where profile_id = %s 
               and channel_id = %s"""

        if type(channel) != type(1):
            channel = self._getChanID(channel)
                    
        self.cursor.execute(q, (pid, channel))
        self._updateInstalledPackages(pid)
        self.conn.commit()

    def listSystems(self):
        q = """select name, uuid from PROFILE"""

        self.cursor.execute(q)
        r = resultSet(self.cursor)
        
        return r.dump()

    def getSystemCount(self):
        q = """select count(*) from PROFILE"""

        self.cursor.execute(q)
        r = self.cursor.fetchone()

        return r[0]
    
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

    def addInstalledPackages(self, pid, package_list):
        """Add a list of packages to the profile."""

        for (name,version,release,epoch) in package_list:
            q = """insert into INSTALLED (profile_id,
                           name, version, release, epoch) values
                           (%s, %s, %s, %s, %s)"""
            self.cursor.execute(q, (pid, name, version, release, epoch))

        self._updateInstalledPackages(pid)
        self.conn.commit()

    def deleteInstalledPackages(self, pid, package_list):
        """Remove a list of packages from the profile."""

	if package_list == None:
	    q = """delete from INSTALLED where profile_id = %s"""
            self.cursor.execute(q, (pid))
	else:
            for pkg in package_list:
                (name,version,release,epoch) = pkg
                q = """delete from INSTALLED where profile_id = %s and
                       name = %s and version = %s and INSTALLED.release = %s
		       and epoch = %s"""
                self.cursor.execute(q, (pid, name, version, release, epoch))
            self._updateInstalledPackages(pid)

        self.conn.commit()

    def updateAllInstallPackages(self):
        """ Update the installed base for all profiles"""

        self.cursor.execute('select profile_id from PROFILE')
        # make a copy of the resulting pids, since we reuse the cursor
        # in the called function. (I love reference objects :( )
        pids = []
        for p in resultSet(self.cursor):
           pids.append(p['profile_id'])
        for p in pids:
            self._updateInstalledPackages(p)

    def _updateInstalledPackages(self, pid):
        """Update the INSTALLED packages for specified profile.
           Instead of the previous versions, we build a list of
           all nvre tuples, and run RPM.versioncompare over it.
           This means we only have 1 or 2 database queries te fetch
           all the needed information. O(n) -> O(1).

           Oh, memory requirements are not so bad. The list contains
           only the nvre tuples a profile is subscribed to and the
           tuples it has installed. (appr. 2x1500 for a full install)"""

        # Q: do we still need to generate the package_id information?
        # It seems to me the newly added info field tells us already
        # if the package is something we have to deal with. The reference
        # to the internal package_id seems superflucios.
#        log('Starting calculations for INSTALLED.package_id',DEBUG)
#
#        # Build a list of all INSTALLED package_id's which need to be changed
#        self.cursor.execute("""select installed_id,PACKAGE.package_id
#                               from SUBSCRIPTIONS
#                                    inner join CHANNEL_RPM using(channel_id)
#                                    inner join RPM using(rpm_id)
#                                    inner join PACKAGE using(package_id),
#                                    INSTALLED
#                               where SUBSCRIPTIONS.profile_id = %s and
#                                    PACKAGE.name = INSTALLED.name and
#                                    PACKAGE.version = INSTALLED.version and
#                                    PACKAGE.release = INSTALLED.release and
#                                    PACKAGE.epoch = INSTALLED.epoch and
#                                    INSTALLED.profile_id = SUBSCRIPTIONS.profile_id and
#                                    not (PACKAGE.package_id <=> INSTALLED.package_id)
#                               """, (pid,))
#
#        log('Doing the update thing',DEBUG)
#
#        # iterate over them and change INSTALLED.package_id
#        for (id,pkg) in list(self.cursor.fetchall()):
#             log("updating %s.package to %s" % (id,pkg), DEBUG)
#            self.cursor.execute("""update INSTALLED set package_id = %s
#                                   where installed_id = %s""", (pkg,id))

        log('Starting calculations for INSTALLED.info for profile %s' % pid,DEBUG)

        # get a list of all active packages for this profile
        self.cursor.execute('''select distinct PACKAGE.name, PACKAGE.version,
                                      PACKAGE.release, PACKAGE.epoch,
                                      -1
                               from   SUBSCRIPTIONS
                               inner  join CHANNEL_RPM_ACTIVE using (channel_id)
                               inner  join RPM using (rpm_id)
                               inner  join PACKAGE using (package_id)
                               where  SUBSCRIPTIONS.profile_id = %s''',
                            (pid,))
        query = list(self.cursor.fetchall())

        # get a list of all INSTALLED packages for this profile
        self.cursor.execute('''select INSTALLED.name, INSTALLED.version,
                                      INSTALLED.release, INSTALLED.epoch,
                                      INSTALLED.installed_id
                               from   INSTALLED
                               where  INSTALLED.profile_id = %s''',
                            (pid,))
	query.extend(list(self.cursor.fetchall()))

        # Sort the list according to RPM.nameversionCompare() results
        # We construct the lambda backwards so that it's actually sorted in
        # reverse order...
        query.sort(lambda x,y: RPM.nameversionCompare((y[0], y[3], y[1], y[2]), (x[0], x[3], x[1], x[2])))

        # per name we can have 5 possibilities:
        # a) first two packages: PACKAGE same as INSTALLED; good
        # b) first two packages: PACKAGE older than INSTALLED; weird stuff
        # c) first two packages: PACKAGE newer then INSTALLED; updatable
        # d) only one package: PACKAGE; installable
        # e) only one package: INSTALLED; orphed package
        # all other with the same name are oldies

        log('Doing the actual update thing',DEBUG)

        # clear the flags field
        self.cursor.execute('''update INSTALLED set info = %s
                               where profile_id = %s''',(OLDIE,pid))

	iname = 0
        index = 0
        first_installed = first_available = -1
        # add a sentinal at the end to correctly process last package
        query.append( ('','','','',-1) )
        for row in query:
            # per name we keep track of the first package and the first
            # installed tuple. We need to compare them later on. Since
            # the list is nvre sorted, the first ones are the newest.
            if row[0] != query[iname][0]:
                if index != iname+1:
                    # case a,b or c
                    cmp = RPM.versionCompare(query[first_available][1:4],query[first_installed][1:4])
                    if cmp == 0:
                        # case a
                        flag = UP2DATE
                    elif cmp<0:
                        # case b
                        flag = EXTRA
                    elif cmp>0:
                        # case c
                        flag = UPDATABLE
#                    log('%s.info = %s' % (query[first_installed][0],flag), DEBUG)
                    self.cursor.execute('''update INSTALLED set info = %s
                                           where installed_id = %s''',
                                        (flag,query[first_installed][4]))
                else:
                    # case d or e
                    if first_installed != -1:
                        # case e
#                        log('%s.info = %s' % (query[iname][0],ORPHANED), DEBUG)
                        self.cursor.execute('''update INSTALLED set info = %s
                                               where installed_id = %s''',
                                            (ORPHANED,query[first_installed][4]))
                iname = index
                first_installed = first_available = -1

            if first_installed<0 and row[4] != -1:
                first_installed = index
            if first_available<0 and row[4] == -1:
                first_available = index
            index=index+1
