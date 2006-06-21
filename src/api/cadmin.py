""" Implement the administrative api calls for current itself.

Notice that these API calls have nothing to do with up2date or RHN - they
are purely an invention of current.

Copyright 2002, 2006 Hunter Matthews, Jack Neely

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

"""

__all__ = ['status']

import string
import sys
import pprint

from logger import *
from sessions import Session
from exception import *
import profiles
import channels
import auth
import configure

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'status',
    'createChannel',
    'addChannelPath',
    'scanChannels',
    'deleteSystem',
    'subscribe',
    'unsubscribe',
    'findProfile',
    'login',
    ]

def login(username, password):
    # This is over SSL, right?  RIGHT?

    # la-la-la lookin' user up in DB la-la-la

    sess = Session()
    sess['userid'] = username
    sess.save()

    return sess.sid


def scanChannels(chanlist):
    result = {}
    logfunc(locals())
    chanlib = channels.Channels()
    
    for chan in chanlist['channels']:
        result[chan] = chanlib.updateChannel(chan)

    return result

def createChannel(channel):
    result = {}
    logfunc(locals())
    chanlib = channels.Channels()

    # Here we might do some sanity checking, but I'm not sure what we'd need.
    result['msg'] = chanlib.makeChannel(channel)
    result['call'] = "Backend call returned without error"
    result['status'] = "ok"
    log("Exiting mkchannel", TRACE)
    log(str(result))

    return result

def addChannelPath(channel):
    result = {}
    logfunc(locals())
    chanlib = channels.Channels()

    # We'll definitely want to do some sanity checking here (eventually)
    for dir in channel['dirs']:
        result[dir] = chanlib.addDir(channel['label'], dir)

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

def deleteSystem(uuid):
    # Remove the related system profile
    p = profiles.Profile(uuid)
    p.delete()
    
    return True

def unsubscribe(uuid, channel):
    # Subscribe the system identifyed by uuid to the given textual channel
    # label
    p = profiles.Profile(uuid)
    p.unsubscribe(channel)
    
    return True

def subscribe(uuid, channel):
    # Subscribe the system identifyed by uuid to the given textual channel
    # label
    p = profiles.Profile(uuid)
    p.subscribe(channel)
    
    return True

def findProfile():
    # Return UUIDs of systems with matching profile name
    # XXX: a regex or something?
    systems = profiles.Systems()
    return systems.search()
    
## END OF LINE ##
