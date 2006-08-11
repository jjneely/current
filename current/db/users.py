#!/usr/bin/python
#
# users.py - Client users interface
#
# Copyright 2006 Pauline Middelink <middelink@polyware.nl>
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

class CurrentProfileDB(CurrentDB):
    pass

class UserDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()


    def getUserID(self, user):
        q = "select user_id from USER where username = %s"
        self.cursor.execute(q, (user,))
        
        result = resultSet(self.cursor)
        if result.rowcount() is 0:
            return None
        
        return result['user_id']
    
    def getUser(self, id):
        q = """select username, password
               from USER where user_id = %s"""

        self.cursor.execute(q, (id,))
        r = self.cursor.fetchone()
        
        # if r is None that's what we want
        return r

    def delete(self, pid):
        "Remove a user"

	# this has to delete the user (duh), the profiles it
	# owns, and the records from installed, hardware,
	# subscriptions.

        self.conn.commit()

    def addUser(self, user, passwd):
        "Add a user"

	self.cursor.execute('''insert into USER (username,password)
			       values(%s,%s)''', (user, passwd))
        self.conn.commit()
	return self.getUserID(user)
