#!/usr/bin/python
#
# xmlrpc.py - XMLRPC helper functions
# Copyright 2004 Jack Neely
# Written by Jack Neely <jjneely@gmail.com>
#
# Parts copyrighted by the following:
# Copyright (c) 1999-2001 by Secret Labs AB
# Copyright (c) 1999-2001 by Fredrik Lundh
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

import xmlrpclib
import gzip

def fileDump(cursor, filename, gz=0, encoding=None):
    """
    Very ripped off from Python's xmlrpclib module.  We need to be able
    to parse large lists of packages sanely and dump that into a 
    compressed file.  We don't want to have to suck the entire dataset
    into memory.

    cursor is assumed to have just executed the proper SQL to generate
       the ordered dataset to dump into filename.  When gzip is true
       this file will be compressed.  See below for encoding.

    encoding: the packet encoding (default is UTF-8)
    """

    if not encoding:
        encoding = "utf-8"

    if gz:
        fd = gzip.GzipFile(filename, 'wb', 9)
    else:
        fd = open(filename, "w")

    m = xmlrpclib.Marshaller(encoding)
    # The Marshler doesn't like to work this particular way
    m.write = fd.write

    if encoding != "utf-8":
        xmlheader = "<?xml version='1.0' encoding=%s?>\n" % repr(encoding)
    else:
        xmlheader = "<?xml version='1.0'?>\n" # utf-8 is default

    # a method response
    fd.write(xmlheader)
    fd.write("<methodResponse>\n")
    fd.write("<params>\n<param>\n")
    fd.write("<value><array><data>\n")

    # don't suck the entire data set into memory at once
    row = cursor.fetchone()
    while not row == None:
        if type(row) != tuple and type(row) != list:
            # sqlite makes up a new sequence type
            row = tuple(row)
        
        try:
            m.dump_array(row)
        except TypeError, e:
            # In Python 2.3...
            m.dump_array(row, fd.write)
            
        row = cursor.fetchone()

    fd.write("</data></array></value>\n")
    fd.write("</param>\n</params>\n")
    fd.write("</methodResponse>\n")
    
    fd.close()
    
