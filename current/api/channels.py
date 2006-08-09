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
from current import auth
from current import profiles
from current import channels

__current_api__ = [
    'systemTotal',
]

def example(sysid_string):
    si = auth.SysId(sysid_string)
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

