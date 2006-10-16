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
import xmlrpclib

from current.logger import *
from current.exception import *
from current.users import SessionUser, User
from current.ou import OU
from current import profiles
from current import channels
from current import auth
from current import configure

# Failed Auth error code
EAUTH = 17

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
    'createUser',
    'showTree',
    ]

def login(username, password):
    # This is over SSL, right?  RIGHT?

    u = SessionUser()
    sessid = u.login(username, password)

    # sessid a coded tuple for us
    return sessid

def createUser(sess, username, password, ou, email):
    # SSL, right?
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    new = User()
    new.newUser(username, password, ou, email)
    # Will raise exception if username already exists.
    return True

def scanChannels(sess, chanlist):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    result = {}
    logfunc(locals())
    chanlib = channels.Channels()
    
    for chan in chanlist['channels']:
        result[chan] = chanlib.updateChannel(chan)

    # we need to re-calculate the state of the INSTALLED packages
    p = profiles.Profile()
    p.updateAllInstallPackages()

    return result

def createChannel(sess, channel):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

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

def addChannelPath(sess, channel):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

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

def deleteSystem(sess, uuid):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    # Remove the related system profile
    p = profiles.Profile(uuid)
    p.delete()
    
    return True

def unsubscribe(sess, uuid, channel):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    # Subscribe the system identifyed by uuid to the given textual channel
    # label
    p = profiles.Profile(uuid)
    p.unsubscribe(channel)
    
    return True

def subscribe(sess, uuid, channel):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    # Subscribe the system identifyed by uuid to the given textual channel
    # label
    p = profiles.Profile(uuid)
    p.subscribe(channel)
    
    return True

def findProfile(sess, pid=None):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    # Return UUIDs of systems with matching profile name
    # XXX: a regex or something?
    systems = profiles.Systems()
    return systems.search(pid)
   
def showTree(sess):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    oulib = OU()
    return oulib.showTree()

## END OF LINE ##
