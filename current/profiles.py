#!/usr/bin/python
#
# profiles.py - Manage profiles for each machine
#
# Copyright 2006 Jack Neely <jjneely@gmail.com>
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
from current.db import profile
from current.logger import *

class Profile(object):

    def __init__(self, id=None):
        self.db = profile.ProfileDB()
        self.pid = None
        
        if id == None:
            # New object
            return

        if len(id.split('-')) == 5:
            self.pid = self.db.getProfileID(id)
        elif id.find("-") == -1:
            self.pid = int(id)
        else:
            log(TRIVIA, "type of id: %s" % str(type(id)))
            raise CurrentException("Badly formed ID.")
        
        if self.pid == None:
            raise CurrentException("No profile found for id: %s" % id)

        self.__load()

    def __load(self):
        # intername helper function.  Reveal profile info
        tup = self.db.getProfile(self.pid)
        if tup == None:
            raise CurrentException("Tried to load an invaild profile id: %s" \
                                   % self.pid)
            
        (self.user_id, self.architecture, self.os_release, self.name, 
         self.release_name, self.uuid) = tup
            
    def __sanity(self):
        if self.pid is None or self.uuid is None:
            raise CurrentExeception("Cannot delete unknown profile.")

    def newProfile(self, user, architecture, os_release, name, release_name, uuid):
        """Create a new profile:
            architecture = platform (ie i686-redhat-linux)
            os_release = Major version of OS (ie 3ES)
            name = profile display name
            release_name = Name of *-release package (defines distribution)
            uuid = OSF DCE 1.1 UUID
        """

        if self.pid != None:
            raise CurrentException("Profile object already contains profile.")
        
        self.pid = self.db.addProfile(user, architecture, os_release, 
                                      name, release_name, uuid)
        self.db.setupBaseChannels(self.pid)

        self.__load()
       
    def delete(self):
        """Remove profile from database."""
        
        self.__sanity()
        
        self.db.delete(self.pid)
        self.pid = None

    def subscribe(self, channel):
        # channel may be the label or the ID
        self.__sanity()
        
        # XXX: is channel valid?  Are we already subscribed?
        self.db.subscribe(self.pid, channel)

    def unsubscribe(self, channel):
        self.__sanity()
        
        self.db.unsubscribe(self.pid, channel)

    def getAuthorizedChannels(self):
        self.__sanity()
        return self.db.getAuthorizedChannels(self.uuid)
    
    def getChannels(self):
        self.__sanity()
        return self.db.getChannels(self.pid)
    
    def addInstalledPackages(self, package_list):
        self.__sanity()
        return self.db.addInstalledPackages(self.pid, package_list)

    def deleteInstalledPackages(self, package_list):
        self.__sanity()
        return self.db.deleteInstalledPackages(self.pid, package_list)

    def updateAllInstallPackages(self):
        return self.db.updateAllInstallPackages()

    def getDetail(self):
        self.__sanity()
        system = self.db.listSystems(self.pid)[0]
        system['num_old_packages'] = self.db.getNumUpdatable(self.pid)
        status = self.db.getStatus(self.pid)
        for key in ['hostname', 'ipaddr', 'kernel', 'uptime', 'checkin']:
            if status.has_key(key):
                system[key] = status[key]
            else:
                system[key] = ""

        return system

    def setStatus(self, hostname, ipaddr, kernel, uptime):
        self.__sanity()
        self.db.setStatus(self.pid, hostname, ipaddr, kernel, uptime)

class Systems(object):

    def __init__(self):
        self.db = profile.ProfileDB()

    def search(self, pid=None):
        # What else does this do?
        # Only systems that a user can see/access to?

        return self.db.listSystems(pid)

    def systemCount(self):
        return self.db.getSystemCount()

    def validUUID(self, uuid):
        if self.db.getProfileID(uuid) == None:
            return False
        else:
            return True

