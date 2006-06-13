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

from exception import *
import db.profile

class Profile(object):

    def __init__(self, id=None):
        self.db = db.profile.ProfileDB()
        self.pid = None
        
        if id == None:
            # New object
            return

        # What is our ID?
        if id.startswith("Current-"):
            # Current-style id from systemid
            self.pid = int(id[8:])
        else:
            # We assume uuid
            self.pid = self.db.getProfileID(id)
            if self.pid == None:
                raise CurrentException("No profile found for id: %s" % id)

        self.__load()

    def __load(self):
        # intername helper function.  Reveal profile info
        tup = self.db.getProfile(self.pid)
        if tup == None:
            raise CurrentException("Tried to load an invaild profile id: %s" \
                                   % self.pid)
            
        (self.architecture, self.os_release, self.name, self.release_name, 
            self.uuid) = tup
            
    def newProfile(self, architecture, os_release, name, release_name, uuid):
        """Create a new profile:
            architecture = platform (ie i686-redhat-linux)
            os_release = Major version of OS (ie 3ES)
            name = profile display name
            release_name = Name of *-release package (defines distribution)
            uuid = OSF DCE 1.1 UUID
        """

        if self.pid != None:
            raise CurrentException("Profile object already contains profile.")
        
        self.pid = self.db.addProfile(architecture, os_release, 
                                      name, release_name, uuid)
        self.__load()
        
