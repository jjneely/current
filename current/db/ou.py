#!/usr/bin/python
#
# ou.py - Database code for the Org Unit tree
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

from types import *

from current.exception import *
from current import db
from current.db.resultSet import resultSet
from current.logger import *

class OUDB(object):

    def __init__(self):
        self.conn   = db.sdb.getConnection()
        self.cursor = db.sdb.getCursor()

    def getRootID(self):
        # Apperently, MySQL has this thing about an auto_increment field
        # starting at 0.  Let's support the ou_id of the root being 
        # whatever the database makes up.
        q = """select ou_id from OU, 
               (select MAX(rgt) as maxrgt from OU) as subselect
               where OU.lft = 0 and OU.rgt = subselect.maxrgt"""

        self.cursor.execute(q)
        if self.cursor.rowcount != 1:
            log(WARNING, "Database curruption.  Got rowcount=%s for root node" \
                % self.cursor.rowcount)
            raise CurrentOUError("Could not locate root OU ID")

        return self.cursor.fetchone()[0]

    def getOUID(self, label):
        q1 = """select count(*) from OU where ou_id = %s"""
        q2 = """select ou_id from OU where label = %s"""

        if isinstance(label, IntType) or isinstance(label, LongType):
            self.cursor.execute(q1, (label,))
            r = self.cursor.fetchone()
            if r[0] > 0:
                return label
            else:
                return None
        else:
            self.cursor.execute(q2, (label,))
            r = self.cursor.fetchone()
            if self.cursor.rowcount == 0:
                return None
            else:
                return self.cursor.fetchone()[0]

    def insertOU(self, parent, label, desc):
        """Insert an OU that will be a child of the given parent OU."""
        # XXX: This can be done entirely in SQL if SQLite can do variables
        # like @varname := foo

        if self.getOUID(parent) == None:
            raise CurrentOUError("Invalid OU ID.")

        # select the rgt value of the parent
        self.cursor.execute("select rgt from OU where ou_id = %s", (parent,))
        prgt = self.cursor.fetchone()[0]

        # add 2 to  all lft/rgt values >= prgt
        q1 = """update OU set lft = lft + 2 where lft >= %s"""
        q2 = """update OU set rgt = rgt + 2 where rgt >= %s"""
        self.cursor.execute(q1, (prgt,))
        self.cursor.execute(q2, (prgt,))

        # create new nodes lft/rgt values
        lft = prgt
        rgt = lft + 1

        q = """insert into OU (label, description, lft, rgt) values
               (%s, %s, %s, %s)"""
        log(DEBUG2, "SQL: %s" % q)
        log(DEBUG2, "(%s, %s, %s, %s)" % (label, desc, lft, rgt))
        self.cursor.execute(q, (label, desc, lft, rgt))

        q = """select ou_id from OU where lft = %s and rgt = %s"""
        self.cursor.execute(q, (lft, rgt))
        ret = self.cursor.fetchone()[0]

        self.conn.commit()

        return ret

    def isChild(self, parent, child):
        """Returns True if child is in the subtree rooted at parent."""

        parent = self.getOUID(parent)
        child = self.getOUID(child)

        if parent == None:
            raise CurrentOUError("Invalid OU ID for parent.")
        if child == None:
            raise CurrentOUError("Invalid OU ID for child.")

        q = """select count(*) from OU as node, OU as parent w
                  where parent.ou_id = %s 
                  and node.ou_id = %s
                  and node.lft between parent.lft and parent.rgt"""

        self.cursor.execute(q, (parent, child))
        return self.cursor.fetchone()[0] > 0

    def subTree(self, root):
        log(TRIVIA, "Pulling subtree of %s, type %s" % (root, type(root)))
        root = self.getOUID(root)
        if root == None:
            raise CurrentOUError("Invalid OU ID.")

        q = """select node.label, node.ou_id,
                  (count(parent.label) - (sub_tree.depth + 1)) as depth
               from OU as node,
                  OU as parent,
                  OU as sub_parent,
                  (   select node.ou_id as ou_id, 
                      (count(parent.label) - 1) as depth
                      from OU as node, OU as parent
                      where node.lft between parent.lft and parent.rgt
                      and node.ou_id = %s
                      group by node.label
                      order by node.lft
                  ) as sub_tree
               where node.lft between parent.lft and parent.rgt
               and node.lft between sub_parent.lft and sub_parent.rgt
               and sub_parent.ou_id = sub_tree.ou_id
               group by node.label
               order by node.lft"""

        self.cursor.execute(q, (root,))
        return resultSet(self.cursor).dump()
