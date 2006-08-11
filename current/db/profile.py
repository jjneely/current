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
from current.logger import *
from current.archtab import *

class CurrentProfileDB(CurrentDB):
    pass

class ProfileDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()
        self.conn.create_function("getArch", 1, getArch)

    def getArch(arch):
	return getCannonArch(arch)

    def addProfile(self, user, arch, os_release, name, release_name, uuid):
        q = """insert into PROFILE (profile_id, user_id, architecture, 
               os_release, name,
               release_name, uuid) values
               (NULL, %s, %s, %s, %s, %s, %s)"""
               
        t = (user, arch, os_release, name, release_name, uuid)

        self.cursor.execute(q, t)
        self.conn.commit()

        return self.getProfileID(uuid)


    def getProfileID(self, uuid):
        q = "select profile_id from PROFILE where uuid = %s"
        self.cursor.execute(q, (uuid,))
        
        result = resultSet(self.cursor)
        if result.rowcount() is 0:
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
               getArch(PROFILE.architecture) = CHANNEL.arch and
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

        if type(channel) == type(1):
            q = """insert into SUBSCRIPTIONS (profile_id, channel_id) values
                   (%s, %s)"""
        else:
            q = """insert into SUBSCRIPTIONS (profile_id, channel_id)
                   select %s, channel_id from CHANNEL where label = %s"""

        self.cursor.execute(q, (pid, channel))
        self.conn.commit()
        
    def unsubscribe(self, pid, channel):
        """Unsubscribe a profile from a channel."""

        q = """delete from SUBSCRIPTIONS where profile_id = %s 
               and channel_id = %s"""

        if type(channel) != type(1):
            channel = self._getChanID(channel)
                    
        self.cursor.execute(q, (pid, channel))
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

    def addPackage(self, pid, subchans, name, version, release, epoch):
        """Add a package to the profile."""

	fmt = """select distinct PACKAGE.package_id from PACKAGE,RPM,CHANNEL_RPM_ACTIVE
	       where ("""
	for chan in subchans:
	  fmt = fmt + "CHANNEL_RPM_ACTIVE.channel_id=%d or " % (chan)
	fmt = fmt + """0) AND CHANNEL_RPM_ACTIVE.rpm_id = RPM.rpm_id AND
		RPM.package_id = PACKAGE.package_id AND
		name=%s AND version=%s AND release=%s and epoch=%s"""
	self.cursor.execute(fmt, (name, version, release, epoch))
	pkg = resultSet(self.cursor)
	if pkg.rowcount() <> 0:
		pkg = pkg['package_id']
	else:
		pkg = None

        q = """insert into INSTALLED (profile_id, package_id,
		name, version, release, epoch) values
               (%s, %s, %s, %s, %s, %s)"""

        self.cursor.execute(q, (pid, pkg, name, version, release, epoch))
        self.conn.commit()

    def deletePackage(self, pid, name, version, release, epoch):
        """Remove a package from the profile."""

	if name == None:
	   q = """delete from INSTALLED where profile_id = %s"""
           self.cursor.execute(q, (pid))
	else:
           q = """delete from INSTALLED where profile_id = %s AND
                name = %s AND version = %s AND release = %s AND
		epoch = %s"""
           self.cursor.execute(q, (pid, name, version, release, epoch))

        self.conn.commit()
