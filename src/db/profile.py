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

from exception import CurrentException
import db
from db.resultSet import resultSet

class CurrentProfileDB(CurrentException):
    pass

class ProfileDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()


    def addProfile(self, systemDict):
        # systemDict should be the same dict passed to register.new_system
        # return system_id
        
        s = systemDict
        q = """insert into PROFILE (architecture, os_release, name,
               release_name, rhnuuid, username) values
               (%s, %s, %s, %s, %s, %s)"""
               
        t = (s['architecture'],
             s['os_release'], s['profile_name'], s['release_name'],
             s['rhnuuid'], s['username'])

        self.cursor.execute(q, t)
        self.conn.commit()

        return self.getProfileID(s['profile_name'])


    def getProfileID(self, profileName):
        q = "select profile_id from PROFILE where name = %s"
        self.cursor.execute(q, (profileName,))
        
        return resultSet(self.cursor)['profile_id']
    
