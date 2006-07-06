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
import socket
import httplib
import urllib2
from xmlrpclib import Fault

from current.logger import *
from current.exception import *

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
   

def _(s):
    # Incase we ever do translations
    return s

def doCall(method, *args, **kwargs):
    """Wrap and Error check XMLRPC calls.
       This was taken from up2date's rpcServer.py and reduces our dependancy
       on up2date which wont always be present."""
    
    ret = None

    attempt_count = 1
    attempts = 5 # XXX: Configurable

    while 1:
        failure = 0
        ret = None        
        try:
            ret = apply(method, args, kwargs)
        except KeyboardInterrupt:
            raise CurrentRPCError(_(
                "Connection aborted by the user"))
        # if we get a socket error, keep tryingx2
        except (socket.error, socket.sslerror), e:
            log("A socket error occurred: %s, attempt #%s" % (
                e, attempt_count), VERBOSE)
            if attempt_count >= attempts:
                if len(e.args) > 1:
                    raise CurrentRPCError(e.args[1])
                else:
                    raise CurrentRPCError(e.args[0])
            else:
                failure = 1
        except httplib.IncompleteRead:
            #print "httplib.IncompleteRead" 
            raise CurrentRPCError("httplib.IncompleteRead")

        except urllib2.HTTPError, e:
            msg = "\nAn HTTP error occurred:\n"
            msg = msg + "URL: %s\n" % e.filename
            msg = msg + "Status Code: %s\n" % e.code
            msg = msg + "Error Message: %s\n" % e.msg
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

# I've added the following
        except xmlrpclib.ProtocolError, e:
            msg = "An XMLRPC protocol error occured: %s" % str(e)
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

        except xmlrpclib.ResponseError, e:
            msg = "Server send a broken responce: %s" % str(e)
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

# XXX: The following is very RHN Server specific.  We are talking to Current.
#       except rpclib.ProtocolError, e:
#           
#           log("A protocol error occurred: %s , attempt #%s," % (
#               e.errmsg, attempt_count), VERBOSE)
#           (errCode, errMsg) = rpclib.reportError(e.headers)
#           reset = 0
#           if abs(errCode) == 34:
#               log("Auth token timeout occurred\n errmsg: %s" % errMsg,
#                   VERBOSE)
#               # this calls login, which in tern calls doCall (ie,
#               # this function) but login should never get a 34, so
#               # should be safe from recursion
#
#               rd = repoDirector.initRepoDirector()
#               rd.updateAuthInfo()
#               reset = 1
#
#           # the servers are being throttle to pay users only, catch the
#           # exceptions and display a nice error message
#           if abs(errCode) == 51:
#               log(_("Server has refused connection due to high load"),
#                   VERBOSE)
#               raise CurrentRPCError(e.errmsg)
#           # if we get a 404 from our server, thats pretty
#           # fatal... no point in retrying over and over. Note that
#           # errCode == 17 is specific to our servers, if the
#           # serverURL is just pointing somewhere random they will
#           # get a 0 for errcode and will raise a CommunicationError
#           if abs(errCode) == 17:
#               #in this case, the args are the package string, so lets try to
#               # build a useful error message
#               if type(args[0]) == type([]):
#                   pkg = args[0]
#               else:
#                   pkg=args[1]
#                   
#               if type(pkg) == type([]):
#                   pkgName = "%s-%s-%s.%s" % (pkg[0], pkg[1], pkg[2], pkg[4])
#               else:
#                   pkgName = pkg
#               msg = "File Not Found: %s\n%s" % (pkgName, errMsg)
#               log(msg, VERBOSE)
#               raise CurrentRPCError(msg)
#               
#           if not reset:
#               if attempt_count >= attempts:
#                   raise CurrentRPCError(e.errmsg)
#               else:
#                   failure = 1
#           
#       except rpclib.ResponseError:
#           raise CurrentRPCError(
#               "Broken response from the server.")

        if ret != None:
            break
        else:
            failure = 1


        if failure:
            # rest for five seconds before trying again
            time.sleep(5)
            attempt_count = attempt_count + 1
        
        if attempt_count > attempts:
            print "busted2"
            print method
            raise CurrentRPCError(
                    "The data returned from the server was incomplete")

    return ret
    
