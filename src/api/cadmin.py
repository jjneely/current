""" Implement the administrative api calls for current itself.

Notice that these API calls have nothing to do with up2date or RHN - they
are purely an invention of current.

Copyright 2002 Hunter Matthews

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

"""

__all__ = ['status']

import string
import sys
import pprint

from logger import *
import auth
import configure
import db

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'status',
    'createChannel',
    'populateChannel',
    'scanChannels',
    ]

def scanChannels(chanlist):
    result = {}
    logfunc(locals())

    for chan in chanlist['channels']:
        result[chan] = db.db.scanChannel(configure.config, chan)
    return result

def createChannel(channel):
    result = {}
    logfunc(locals())

    # Here we might do some sanity checking, but I'm not sure what we'd need.
    try:
        result['msg'] = db.db.makeChannel(configure.config, channel)
        result['call'] = "Backend call returned without error"
        result['status'] = "ok"
        log("Exiting mkchannel")
        log(str(result))

    except Exception, e:
        result['call'] = "Function call blew up.  Bad day."
        result['status'] = e
    return result

def populateChannel(channel):
    result = {}
    logfunc(locals())

#    # this bit has GOT to change...
#    if channel['bin'][0] == '':
#         channel['bin'] = []
#     if channel['src'][0] == '':
#         channel['src'] = []

    # We'll definitely want to do some sanity checking here (eventually)
    for dir in channel['dirs']:
        result[dir] = db.db.addDir(channel['label'], dir
)
#     for dir in channel['bin']:
#         # This is where sanity checking (i.e. does this dir exist?) should go
#         result[dir] = db.db.addDir(channel['label'], dir, 1)
#     for dir in channel['src']:
#         # Likewise
#         result[dir] = db.db.addDir(channel['label'], dir, 0)

    result['status'] = "ok"
    return result


def status():
    """ Get some information about the server itself. """

    logfunc(locals())

    # Authorize the client
#     si = auth.SysId()
#     si.loadstring(sysid_string)
#     if not si.isValid():
#         return xmlrpclib.Fault(1000, "Invalid client certificate.")

    # we hand back a dict with the information
    status = {}

    # python version and some other junk
    status['python_executable'] = sys.executable
    status['python_path'] = sys.path
    try:
        status['python_version'] = sys.version_info
    except:
        status['python_version'] = 'Its too old, Yogi'

    return status


## END OF LINE ##
