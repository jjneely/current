#!/usr/bin/python
#
# yum.py - Yum plugin support
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

import socket
import xmlrpclib

from current.logger import *
from current import auth
from current import profiles

__current_api__ = [
    'getYumConfig',
]

def getYumConfig(sysid_string):
    si = auth.SysId(sysid_string)
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")

    chans = p.getAuthorizedChannels()
    uri = "https://%s/XMLRPC/$RHN/" % (socket.getfqdn())
    yumconf = []

    if len(chans) == 0:
        return xmlrpclib.Fault(1000, 
                               "System is not authorized to any channels.")

    for chan in chans:
        yumconf.append('[%s]' % chan['label'])
        yumconf.append('name=%s' % chan['name'])
        yumconf.append('enabled=1')
        yumconf.append('baseurl=%s%s' % (uri, chan['label']))

    return '\n'.join(yumconf)

