#!/usr/bin/python
#
# sessions.py - DB interface
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

# create table SESSIONS (
#    session_id     INTEGER PRIMARY KEY,
#    sid            varchar(32) unique not null,
#    createtime     float not null,
#    timeout        float not null,
#    data           text
# );
# create index SESSION_IDX on SESSION(sid);

import time

from exception import CurrentSession
import db
from db.resultSet import resultSet

class SessionDB(object):

    def __init__(self):
        self.cursor = db.sdb.getCursor()
        self.conn   = db.sdb.getConnection()

    def load(self, sid):
        q = """select createtime, timeout, data from SESSIONS where
               sid = %s"""

        self.cursor.execute(q, (sid,))
        if self.cursor.rowcount == 0:
            raise CurrentSession("Session not found")

        r = self.cursor.fetchone()
        return r[0], r[1], r[2]
        

    def delete(self, sid):
        q = """delete from SESSIONS where sid = %s"""

        try:
            self.load(sid)
        except CurrentSession:
            # Session doesn't exist
            return
        
        self.cursor.execute(q, (sid,))

        
    def save(self, sid, cTime, timeOut, data):
        self.delete(sid)

        q = """insert into SESSIONS (sid, createtime, timeout, data) 
               values (%s, %s, %s, %s)"""

        self.cursor.execute(q, (sid, cTime, timeOut, data))


    def commit(self):
        self.conn.commit()
        

    def clean(self, delta=3600):
        """Remove old sessions from database.  For safety only delete
           sessions where timeout + delta < time.time()"""

        t = time.time() - delta
        q = """delete from SESSIONS where timeout < %s"""

        self.cursor.execute(q, (t,))


