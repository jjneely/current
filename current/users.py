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
from current.sessions import Session
from current.exception import *
from current.logger import *
from current.db import users
from current import configure

class User(object):

    def __init__(self, user=None):
        self.db = users.UserDB()
        self.pid = None
        self.username = None
        self.password = None
        self.ou = None
        
        if user == None:
            # New object
            return

        if type(user) == str:
            self.pid = self.db.getUserID(user)
            if self.pid == None:
                raise CurrentUser("No user found: %s" % user)
        else:
            self.pid = user

        self._load()

    def _load(self):
        # intername helper function.  Reveal user info
        data = self.db.getUser(self.pid)
        if data == None:
            raise CurrentException("Tried to load an invalid user id: %s" \
                                   % self.pid)
            
        self.username = data['username']
        self.password = data['password']
        self.email = data['email']
        self.ou = data['ou_id']
            
    def __sanity(self):
        if self.pid == None:
            raise CurrentUser("User object is not initialized.")

    def _makePasswd(self, clear):
        s = "Current-%s-%s" % (configure.config['server_secret'], clear)
        crypt = sha.new(s).hexdigest()
        del s
        return crypt

    def isValid(self, password):
        """Check if this combo exists in the database."""

        self.__sanity()
        return self.password == self._makePasswd(password)

    def newUser(self, username, password, ou, email):
        """Create a new user """

        if self.pid != None:
            raise CurrentUser("User object already contains user.")
    
        if self.db.getUserID(username) != None:
            raise CurrentUser("User name already in use.")

        self.pid = self.db.addUser(username, self._makePasswd(password), 
                                   ou, email)
        self._load()
       
    def addInfo(self, product_info):
        """Add contact information to the user"""

        self.__sanity()
        self.db.addInfo(self.pid, product_info)

    def delete(self):
        """Remove user from database."""
        
        self.__sanity()
        
        self.db.delete(self.pid)
        self.pid = None


class SessionUser(User):

    def __init__(self, sess=None):
        self.session = Session(sess, configure.config['server_secret'])

        if self.isValid():
            User.__init__(self, self.session['pid'])
        else:
            User.__init__(self)

    def __initSession(self):
        self.session['pid'] = self.pid
        self.session['userid'] = self.username
        self.session.is_new = False
        self.session.save()

    def __sanity(self):
        if not self.isValid():
            raise CurrentUser("Expired user session.  Please log in.")

        User.__sanity(self)

    def isValid(self):
        if self.session.isValid() and not self.session.isNew():
            return True
        else:
            return False

    def login(self, user, password):
        if not self.session.isNew():
            log(VERBOSE, "BUG: Attempt to reuse SessionUser object")
            raise CurrentUser("BUG: Attempt to reuse SessionUser object")

        self.pid = self.db.getUserID(user)
        if self.pid == None:
            log(DEBUG, "Tried to lookup non-existant user id")

            if self.db.isInitialUser():
                log(VERBOSE, "Creating inital super user")
                self.newUser(user, password, 0, "root@localhost")
                self.__initSession()
                return {'code':1, 'session':self.session.sid}
            else:
                return {'code':-1, 'session':""}

        self._load()

        if User.isValid(self, password):
            self.__initSession()
            return {'code':0, 'session':self.session.sid}
        else:
            return {'code':-1, 'session':""}
