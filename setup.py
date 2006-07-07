#!/usr/bin/python
#
# setup.py - Distutils setup
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

import os
import os.path
from distutils.core import setup

def getDirs(path):
    # Split up a directory listing of files and directories
    dirs = [path.replace('/', '.')]

    dir = os.listdir(path)
    for node in dir:
        apath = os.path.join(path, node)
        if ".svn" in apath: 
            continue
        if os.path.isdir(apath):
            dirs.extend(getDirs(apath))

    return dirs

print getDirs('current')

setup(  version="1.7.3",

        name="Current",
        description="An Open Source Up2date Server.",
        author="Jack Neely, Hunter Matthews",
        author_email="users@current.tigris.org",
        url="http://current.tigris.org",

        packages=getDirs('current'),
        data_files=[('/etc/current', ['current.conf'])],
        scripts=['cinstall', 'current/cadmin.py'],
     )
