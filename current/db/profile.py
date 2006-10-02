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

import time

from current.exception import *
from current import db
from current.db.resultSet import resultSet
from current import RPM
from current.logger import *
from current.archtab import *

# Constants used in database schema
OLDIE     = 0 # rpm for which a newer version is also installed (e.g. kernel)
UP2DATE   = 1 # rpm which is as recent as we have
EXTRA     = 2 # installed rpm which is MORE RECENT than we have
UPDATABLE = 3 # rpm for which we have a newer version
ORPHANED  = 4 # rpm of which we dont know anything

class ProfileDB(object):

    def __init__(self):
        self.conn   = db.sdb.getConnection()
        self.cursor = db.sdb.getCursor()

    def addProfile(self, user, arch, os_release, name, release_name, uuid):
        q = """insert into PROFILE (profile_id, user_id, architecture, 
               cannon_arch, os_release, name, release_name, uuid, registered)
               values (NULL, %s, %s, %s, %s, %s, %s, %s, %s)"""
               
        t = (user, arch, getCannonArch(arch), os_release, 
             name, release_name, uuid, time.time())

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
        q = """select user_id, architecture, os_release, name, release_name, 
               uuid from PROFILE where profile_id = %s"""

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
        result = resultSet(self.cursor).dump()
        for row in result:
            self.subscribe(pid, row['channel_id'])

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

    def getChannelLabels(self, pid):
        "Returns the channel labels a given profile ID is subscribed to"

        q = """select label from CHANNEL, SUBSCRIPTIONS where
               CHANNEL.channel_id = SUBSCRIPTIONS.channel_id and
               SUBSCRIPTIONS.profile_id = %s"""

        self.cursor.execute(q, (pid,))

        ret = []
        for row in resultSet(self.cursor):
            ret.append(row['label'])

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

    def setStatus(self, pid, hostname, ipaddr, kernel, uptime):
        q1 = """select status_id from STATUS where profile_id = %s"""
        
        self.cursor.execute(q1, (pid,))
        r = resultSet(self.cursor)
        if r.rowcount() == 0:
            q2 = """insert into STATUS (profile_id, hostname, ipaddr, kernel,
                                        uptime, checkin) values
                                        (%s, %s, %s, %s, %s, %s)"""
            t = (pid, hostname, ipaddr, kernel, uptime, time.time())
        else:
            q2 = """update STATUS set hostname = %s, ipaddr = %s, 
                    kernel = %s, uptime = %s, checkin = %s where
                    status_id = %s"""
            t = (hostname, ipaddr, kernel, uptime, time.time(), r['status_id'])

        self.cursor.execute(q2, t)
        self.conn.commit()

    def getStatus(self, pid):
        q = """select hostname, ipaddr, kernel, uptime, checkin from STATUS
               where profile_id = %s"""

        self.cursor.execute(q, (pid,))
        r = resultSet(self.cursor)

        if r.rowcount() == 0:
            return {}
        else:
            return r.dump()[0]

    def listSystems(self, pid=None):
        q = """select name, uuid, profile_id from PROFILE"""
        if pid != None:
            q = q + " where profile_id = %s"

        if pid == None:
            tup = None
        else:
            tup = (pid,)

        self.cursor.execute(q, tup)
        r = resultSet(self.cursor)
        ret = r.dump()

        for row in ret:
            row['labels'] = self.getChannelLabels(row['profile_id'])

        return ret

    def getSystemCount(self):
        q = """select count(*) from PROFILE"""

        self.cursor.execute(q)
        r = self.cursor.fetchone()

        return r[0]
   
    def getNumUpdatable(self, pid):
        q = """select count(*) from INSTALLED where profile_id = %s
               and info = %s"""

        self.cursor.execute(q, (pid, UPDATABLE))
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


    def _getPackageId(self, name, version, release, epoch, issource):
        #logfunc(locals(), TRACE)
        self.cursor.execute(''' select package_id from PACKAGE
                where name = %s
                and version = %s
                and PACKAGE.release = %s
                and epoch = %s
                and issource = %s''', (name, version, release,
                                       epoch, issource))

        r = resultSet(self.cursor)
        if r.rowcount() == 0:
            return None
        return r['package_id']

    def _insertPackage(self, name, version, release, epoch, issource):
        package_id = self._getPackageId(name, version, release,
                                        epoch, issource)
        if not package_id:
            self.cursor.execute('''insert into PACKAGE
                        (name, version, `release`, epoch, issource)
                        values (%s, %s, %s, %s, %s)''',
                        (name, version, release, epoch, issource))
            # PM2006, we really should be using last_insert_id
            # (maybe make it a general connection method even)
            package_id = self._getPackageId(name, version, release,
                                            epoch, issource)
            if not package_id:
                log("Inserted package but could not lookup package_id", VERBOSE)

        return package_id

    def addInstalledPackages(self, pid, package_list):
        """Add a list of packages to the profile."""

        for (name,version,release,epoch) in package_list:
            package_id = self._insertPackage(name,version,release,epoch,0)
            if package_id:
                q = """insert into INSTALLED (profile_id, package_id)
                               values (%s, %s)"""
                self.cursor.execute(q, (pid, package_id))

        self._updateInstalledPackages(pid)
        self.conn.commit()

    def deleteInstalledPackages(self, pid, package_list):
        """Remove a list of packages from the profile."""

        pkgs = [];
        if not package_list:
                self.cursor.execute('''select package_id from INSTALLED
                                       where profile_id = %s''',
                                    (pid,))
                for p in self.cursor.fetchall():
                    pkgs.append(p[0])

	        self.cursor.execute('''delete from INSTALLED where
                                       profile_id = %s''', (pid,))
        else:
            for (name,version,release,epoch) in package_list:
                package_id = self._getPackageId(name,version,release,epoch,0)
                if package_id:
                    self.cursor.execute('''delete from INSTALLED where
                                         profile_id = %s and package_id = %s''',
                       (pid, package_id))
                    pkgs.append(package_id)

        for (pkg) in pkgs:
            self.cursor.execute('''select count(*) from RPM
                                   where package_id = %s
                                   union all
                                   select count(*) from INSTALLED
                                   where package_id = %s''',
                                (pkg,pkg))
            r = self.cursor.fetchall()
            count = r[0][0] + r[1][0]
#            log("Num of RPMs with package_id=%s: %s" % (pkg, count), DEBUG2)
            if count == 0:
                # We know there are no more references to this PACKAGE
                self.cursor.execute('''delete from PACKAGE where 
                                       package_id = %s''', (pkg,))

        if package_list:
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

        self.conn.commit()

    def _updateInstalledPackages(self, pid):
        """Update the INSTALLED packages for specified profile.
           Instead of the previous versions, we build a list of
           all nvre tuples, and run RPM.versioncompare over it.
           This means we only have 1 or 2 database queries te fetch
           all the needed information. O(n) -> O(1).

           Oh, memory requirements are not so bad. The list contains
           only the nvre tuples a profile is subscribed to and the
           tuples it has installed. (appr. 2x1500 for a full install)"""

        log('Starting calculations for INSTALLED.info for profile %s' % \
            pid, DEBUG)

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
        self.cursor.execute('''select PACKAGE.name, PACKAGE.version,
                                      PACKAGE.release, PACKAGE.epoch,
                                      installed_id
                               from   INSTALLED
                               inner join PACKAGE using (package_id) 
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
