#!/usr/bin/python
#
# sessions.py - Manage sessions for a in a generic manner for both a web
#    interface and an XMLRPC interface
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

import md5
import time
import random
import pickle
from mod_python import Cookie
from current.db import sessions
from current import exception

class Session(dict):

    def __init__(self, sid=None, secret=None):
        """Create a new session.  If sid is not None attempt to load that
           session from the store."""

        dict.__init__(self)
        self.db = sessions.SessionDB()

        if sid == None:
            # create new object
            self.__new(secret)
            return
        
        try:
            self.createTime, self.timeOut, data = self.db.load(sid)
        except exception.CurrentSession:
            self.__new(secret)
            return
        
        if not self.isValid():
            self.__new(secret)
        else:
            d = pickle.loads(data)

            for key in d.keys():
                self[key] = d[key]

            self.is_new = False
            self.sid = sid


    def __new(self, secret):
        self.createTime = time.time()
        self.timeOut = self.createTime + 3600 # default time out 1 hr
        s = "Current-%s-%s" % (str(random.random()), str(secret))
        self.sid = md5.new(s).hexdigest()
        self.is_new = True
        
                                                        
    def isNew(self):
        return self.is_new


    def isValid(self):
        return self.timeOut >= time.time()

    
    def invalidate(self):
        self.setTimeOut(0)


    def setTimeOut(self, secs):
        """Set the time out in seconds since session creation."""

        self.timeOut = secs


    def save(self):
        """Save session to db and clean db"""

        self.db.clean()

        self.setTimeOut(time.time() + 3600)
        
        data = pickle.dumps(dict(self))
        self.db.save(self.sid, self.createTime, self.timeOut, data)
        self.db.commit()


class CookieSession(Session):

    cookieName = "Current-Session"
    
    def __init__(self, req, secret=None):
        self.req = req
        self.__secret = secret
        cookies = Cookie.get_cookies(req, Cookie.SignedCookie,
                                     secret=str(self.__secret))
        
        if cookies.has_key(self.cookieName):
            c = cookies[self.cookieName]
            if type(c) is not Cookie.SignedCookie:
                # Cookie was tampered with...BAD COOKIE!
                Session.__init__(self, None, self.__secret)
                return

            Session.__init__(self, c.value, self.__secret)
            return

        Session.__init__(self, None, secret)


    def save(self):
        Session.save(self)

        c = Cookie.SignedCookie(self.cookieName, self.sid, 
                                str(self.__secret))
        c.expires = time.time() + 3600
        Cookie.add_cookie(self.req, c)

