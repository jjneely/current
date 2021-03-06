""" up2date API for implementing the server side of up2date.

Copyright (c) 2001 Hunter Matthews    Distributed under GPL.

Note: The actual up2date client makes some 'registration' calls as well.

For details on the exact API, what each method expects and what it 
returns, please see the rhn_api.txt file.
"""

import copy
import pprint
import xmlrpclib
import sys

from current import profiles
from current import channels
from current import configure
from current import auth
from current.logger import *
from current.exception import *

__current_api__ = [
    'login',                               ## These are the newer 2.7 API
    'listChannels',
    'solveDependencies',
    'subscribeChannels',
    'unsubscribeChannels',
    ]


def login(sysid_string):

    logfunc(locals())
    chanlib = channels.Channels()

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        log("Fault! - sysid not valid")
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")
    
    # Setup the basic SysHeaders stuff
    hi = auth.SysHeaders()
    hi.loadSysId(si)
    hi.setTimeValues()
    
    # Need a list of channels this client is authorized for 
    # FIXME: we assume only one channel right now is returned...
    chans = chanlib.getCompatibleChannels(si.getattr('architecture'), 
                                                  si.getattr('os_release'))    
    if len(chans) == 0:
        log("Fault! - no channels")
        return xmlrpclib.Fault(1000, 
            "No compatible channels found for client")

    # This is mostly here as a marker - we'd pass in a list of all possible
    #   (compatible) channels, and get back a list (pos. empty) of the ones
    #   this client was authorized to to touch.
    chans = p.getAuthorizedChannels()
    if len(chans) == 0:
        log ("Fault! - not authorized for channels")
        return xmlrpclib.Fault(1000, 
            "Client is not authorized for any channels")

    # Actually append that information to our headerId
    for chan in chans:
        hi.addAuthChannel(chan)

    hi.setChecksum()            
    return hi.dumpLoginInfo()
    

def listChannels(sysid_string):
    """ Send a list of all compatible channels back to client. """

    logfunc(locals())
    chanlib = channels.Channels()

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        log("sysid not valid in listChannels()")
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")
    
    # Need a list of channels this client is authorized for 
    # FIXME: we assume only one channel right now is returned...
    chans = chanlib.getCompatibleChannels(si.getattr('architecture'),
                                                  si.getattr('os_release'))
    if len(chans) == 0:
        return xmlrpclib.Fault(1000, 
            "No compatible channels found for client")

    # This is mostly here as a marker - we'd pass in a list of all possible
    #   (compatible) channels, and get back a list (pos. empty) of the ones
    #   this client was authorized to to touch.
    chans = p.getAuthorizedChannels()
    if len(chans) == 0:
        return xmlrpclib.Fault(1000, 
            "Client is not authorized for any channels")

    # Must not alter the in-memory copy - we need a temp form
    result = copy.deepcopy(chans)

    # Transfer chanInfo structure into API result
    for chan in result:
        for key in chan.keys():
            if key not in ('name', 'parent_channel', 'label', 'arch', 'description'):
                del chan[key]

    return result

        
def solveDependencies(sysid_string, unknowns):
    """ Find all the packages needed to 'provide' these unknown dependancies.

    """

    logfunc({'unknowns': unknowns})    ## cheat: sysid is boring
    chanlib = channels.Channels()

    # Authorize the client
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
    
    chans = chanlib.getCompatibleChannels(si.getattr('architecture'),
                                           si.getattr('os_release'))
    if len(chans) == 0:
        return xmlrpclib.Fault(1000, 
            "No compatible channels found for client")

    # This is mostly here as a marker - we'd pass in a list of all possible
    #   (compatible) channels, and get back a list (pos. empty) of the ones
    #   this client was authorized to to touch.
    chans = p.getAuthorizedChannels()
    if len(chans) == 0:
        return xmlrpclib.Fault(1000, 
            "Client is not authorized for any channels")

    provides = {}
    for unk in unknowns:

        # packagedb.solveDep will return None if our db can't solve that
        # in which case, we return an empty list for that unk, which is what
        # the client expects.
        provides[unk] = []

        # iterate over all channels available to the client
        for chan in chans:
            pkgs = chanlib.solveDependancy(chan['label'], 
                                         si.getattr('architecture'),
                                         unk)

            if pkgs:
                for pkg in pkgs:
                    provides[unk].append(pkg)

    return provides


def subscribeChannels(sysid_string, chans, username, password):

    # Authorize the client
    si = auth.SysId(sysid_string)
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # The client doesn't support this call yet 
    # and we don't have backend support yet anyway

    return 0                                                                                 


def unsubscribeChannels(sysid_string, chans, username, password):

    # Authorize the client
    si = auth.SysId(sysid_string)
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # The client doesn't support this call yet 
    # and we don't have backend support yet anyway

    return 0                                                                                 


## END OF LINE ##    

