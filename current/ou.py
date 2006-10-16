#!/usr/bin/python
#
# ou.py - Application layer for OUs
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
from current.db.ou import OUDB
from current.logger import *

class OU(object):

    def __init__(self):
        self.db = OUDB()

    def getOUID(self, label):
        # Do we want to handle paths, unique labels, or just OU IDs?
        # Raises exception if OU doesn't exist
        return self.db.getOUID(label)

    def isChild(self, parent, child):
        return self.db.isChild(parent, child)

    def insertNode(self, parent, label, desc):
        return self.db.insertNode(parent, label, desc)

    def showTree(self, user=0):
        # The Root OU always has id == 0
        return self.db.subTree(user)

