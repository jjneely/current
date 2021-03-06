#!/usr/bin/python
#
# channels.py - Interface for manipulating channels
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
from current.channels import Channels

# Failed Auth error code
EAUTH = 17

__current_api__ = [
    'listChannels',
    'getChannelDetail',
]

def listChannels(sess):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    chanlib = Channels()
    return chanlib.listChannels()

def getChannelDetail(sess, label):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    chanlib = Channels()
    return chanlib.getChannelDetail(label)

