#!/usr/bin/python
#
# channelss.py - Manage channels
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

from exception import *
from logger import *

import configure
import db

# XXX:
# Big design goal for Current is to have 3 layers:
# 1) The API layer is what cadmin and possibly other tools directly call
# 2) The Application layer is what the API functions call into
# 3) The DB layer ONLY contains database functions
#
# currentdb.py has a LOT of file manipulation that needs to be pulled
# out at some point and should be in this module or another modules at
# the Applications layer.  (Stuff in the top level src/ directory.)
# Right now, the public methods are duplcated here and are just calls
# into the DB layer until we can get this sorted out.

class Channels(object):
    
    def __init__(self):
        self.db = db.db
        self.config = configure.config      # initiated by init_backend()

    def abort(self):
        # XXX: Used in the API layer!  BAD!
        log("GAH: Don't call this function!!", MANDATORY)
        return self.db.abort()
   
    def addDir(self, label, dirs):
        return self.db.addDir(label, dirs)

    def makeChannel(self, channel):
        self.db.makeChannel(channel)
        
        # Now create the directories on disk for this channel
        webdir = os.path.join(self.config['current_dir'], 'www')
        chan_dir = os.path.join(webdir, channel['label'])
        if not os.access(chan_dir, os.W_OK):
            os.mkdir(chan_dir)
            for dir in ['getObsoletes', 'getPackage', 'getPackageHeader',
                        'getPackageSource', 'listPackages', 'listAllPackages']:
                os.mkdir(os.path.join(chan_dir, dir))
        # FIXME: need an else here for error handling

        log("New channel and dirs created.", DEBUG)

        return 0

    def updateChannel(self, channel):
        return self.db.updateChannel(channel)

    def getCompatibleChannels(self, arch, release):
        return self.db.getCompatibleChannels(self, arch, release)

    def solveDependancy(self, label, arch, unknown):
        return self.db.solveDependancy(self, label, arch, unknown)

    def getLastUpdate(self, release, arch):
        return self.db.getLastUpdate(self, release, arch)

    def listAppletPackages(self, release, arch):
        return self.db.listAppletPackages(self, release, arch)
    
