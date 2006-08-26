#!/usr/bin/python
#
# users.py - Manage user
#
# Copyright 2006 Pauline Middelink <middelink@iaf.nl>
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

import sha
from current.exception import *
from current.logger import *
from current.db import users

class Users(object):

    def __init__(self, user=None):
        self.db = users.UserDB()
        self.pid = None
        
        if user == None:
            # New object
            return

        if type(user) == str:
            self.pid = self.db.getUserID(user)
            if self.pid == None:
                raise CurrentException("No user found: %s" % user)
        else:
            self.pid = user

        self.__load()

    def __load(self):
        # intername helper function.  Reveal user info
        tup = self.db.getUser(self.pid)
        if tup == None:
            raise CurrentException("Tried to load an invalid user id: %s" \
                                   % self.pid)
            
        (self.username, self.password, self.email) = tup
            
    def __sanity(self):
        if self.pid is None:
            raise CurrentExeception("Cannot delete unknown user.")

    def isValid(self, password):
        """Check if this combo exists in the database."""

        return self.password == sha.new(password).hexdigest()

    def newUser(self, username, password, email):
        """Create a new user """

        if self.pid != None:
            raise CurrentException("User object already contains user.")
        
        self.pid = self.db.addUser(username, sha.new(password).hexdigest(), email)
        self.__load()
       
    def addInfo(self, product_info):
        """Add contact information to the user"""

        self.db.addInfo(self.pid, product_info)

    def delete(self):
        """Remove user from database."""
        
        self.__sanity()
        
        self.db.delete(self.pid)
        self.pid = None
