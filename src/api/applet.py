""" up2date APPLET API for implementing the server side of the APPLET
    interface in the rhn-applet package

Copyright (c) 2003 John Berninger, Hunter Matthews.
Dsitributed under GPL.

For details on this (admittedly short) API, please see the rhn_api.txt file.
"""

import db
import archtab
from logger import *


__current_api__ = [
    'poll_status',
    'poll_packages'
    ]


def poll_status():
    result = {}
    result['checkin_interval'] = 15360
    result['server_status'] = 'normal'
    return resultr


def poll_packages(release, arch, last_checkin, uuid):
    # release is the release of the client
    # arch is the arch of the client - not necessarily a base arch, tho
    # last_checkin is the last time this client got an updated list.
    # uuid seems to be totally unimportant at this stage.

    carch = archtab.getCannonArch(arch)
    channel_update_time = db.db.getLastUpdate(release, carch)
    
    # If our last_checkin is 0, we need to send a cache regardless of the
    # outcome of the two 'short circuit' if's.
    if ( channel_update_time == -1 and last_checkin != 0):
        # This indicates there was no channel with the proper arch/release
        # combination
        return {'no_packages':0}

    if ( channel_update_time <= last_checkin and last_checkin != 0):
        # This indicates there are no updates.
        return {'use_cached_copy':1}

    # Now we need to build the return cache...
    result = {}
    result['last_modified'] = channel_update_time
    result['contents'] = []
    pkgs = db.db.listAppletPackages(release, carch)
    log ('%s packages returned.' % len(pkgs) )
    for row in pkgs:
        dict = {}
        dict['name'] = row[0]
        dict['version'] = row[1]
        dict['release'] = row[2]
        dict['epoch'] = row[3]
        dict['nvr'] = '%s-%s-%s' % (row[0], row[1], row[2])
        dict['nevr'] = '%s-%s-%s:%s' % (row[0], row[1], row[2], row[3])
        dict['errata_advisory'] = ''
        dict['errata_id'] = ''
        dict['errata_synopsis'] = ''
        result['contents'].append(dict)

    return result 
