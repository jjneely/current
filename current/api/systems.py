#!/usr/bin/python
#
# systems.py - Interface for manipulating systems/profiles
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

from current.logger import *
from current.users import SessionUser
from current import profiles
from current import channels
from cadmin import EAUTH

__current_api__ = [
    'systemCount',
    'systemDetail',
]

def systemCount(sess):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")
    
    syslib = profiles.Systems()
    return syslib.systemCount()

def systemDetail(sess, pid):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    p = profiles.Profile(pid)
    return p.getDetail()

