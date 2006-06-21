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

from exception import *
import db
from db.resultSet import resultSet

class CurrentProfileDB(CurrentDB):
    pass

class ProfileDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()


    def addProfile(self, arch, os_release, name, release_name, uuid):
        q = """insert into PROFILE (profile_id, architecture, 
               os_release, name,
               release_name, uuid) values
               (NULL, %s, %s, %s, %s, %s)"""
               
        t = (arch, os_release, name, release_name, uuid)

        self.cursor.execute(q, t)
        self.conn.commit()

        return self.getProfileID(uuid)


    def getProfileID(self, uuid):
        q = "select profile_id from PROFILE where uuid = %s"
        self.cursor.execute(q, (uuid,))
        
        return resultSet(self.cursor)['profile_id']
    
    def getProfile(self, id):
        q = """select architecture, os_release, name, release_name, uuid
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
               PROFILE.architecture = CHANNEL.arch and
               PROFILE.release = CHANNEL.osrelease"""

        self.cursor.execute(q, (pid,))
        result = resultSet(self.cursor)
        chans = []
        for row in result:
            chans.append(row['channel_id'])

        for c in chans:
            self.subscribe(pid, c)
        
        
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

        if type(channel) == type(1):
            q = """delete from SUBSCRIPTIONS where profile_id = %s 
                   and channel_id = %s"""
        else:
            q = """delete from SUBSCRIPTIONS, CHANNEL where 
                    SUBSCRIPTIONS.profile_id = %s and
                    SUBSCRIPTIONS.channel_id = CHANNEL.channel_id and
                    CHANNEL.label = %s"""
                    
        self.cursor.execute(q, (pid, channel))
        self.conn.commit()

    def listSystems(self):
        q = """select name, uuid from PROFILE"""

        self.cursor.execute(q)
        r = resultSet(self.cursor)
        
        l = []
        for row in r:
            l.append((r['name'], r['uuid']))

        return l

