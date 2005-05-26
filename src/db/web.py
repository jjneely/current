#!/usr/bin/python
#
# web.py - DB interface
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

class CurrentWebDB(CurrentException):
    pass

class WebDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()


    def getChannels(self):
        # Return a dict of information for each channel
        q = "select name, label, description from CHANNEL"
        self.cursor.execute(q)

        return resultSet(self.cursor)
        

    def getAllPackages(self, channel):
        self.cursor.execute('''select PACKAGE.name, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch, 
                RPM.size, CHANNEL.label 
                from PACKAGE, RPM, CHANNEL_RPM, CHANNEL  where
                CHANNEL_RPM.rpm_id = RPM.rpm_id and
                CHANNEL_RPM.channel_id = CHANNEL.channel_id and
                CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                and PACKAGE.issource = 0
                order by PACKAGE.name''', (channel,))

        return resultSet(self.cursor)
    
    
    def getPackages(self, channel):
        self.cursor.execute('''select PACKAGE.name, PACKAGE.version,
                PACKAGE.release, PACKAGE.epoch, RPM.arch, 
                RPM.size, CHANNEL.label 
                from PACKAGE, RPM, CHANNEL_RPM_ACTIVE, CHANNEL where
                RPM.rpm_id = CHANNEL_RPM_ACTIVE.rpm_id
                and CHANNEL_RPM_ACTIVE.channel_id = CHANNEL.channel_id
                and CHANNEL.label = %s
                and PACKAGE.package_id = RPM.package_id
                and PACKAGE.issource = 0
                order by PACKAGE.name''', (channel,))

        return resultSet(self.cursor)


    def getChannelName(self, label):
        q = "select name from CHANNEL where label = %s"
        self.cursor.execute(q, (label,))
        r = resultSet(self.cursor)

        return r['name']

