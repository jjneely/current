""" Implement the queue parts of the RHN api. 

These calls come from the rhn_check client (and rhnsd, which simply calls
rhn_check). queue.get() asks for any actions that the server wishes the 
client to perform. queue.submit() is then called by the client to notify 
the server success/failure.

For details on the exact API, what each method expects and what it 
returns, please see the rhn_api.txt file.

Copyright 2002 Hunter Matthews

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

History: 
Started figuring out some way to get rid of that pesky cron job in 1.5.0.

"""

__author__ = 'Hunter Matthews <thm@duke.edu>'

import xmlrpclib
import string
import pprint

from logger import *
import auth
import config

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'get',
    'submit'
    ]


def get(sysid_string, action_version, client_status):
    """ Send any actions for this particular client from the db. """

    logfunc(locals())

    # Authorize the client
    si = auth.SysId()
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

#     params = 
#     encoded_action = xmlrpclib.dumps(params, packages.upgrade)
#    
#     result = {'id': '777', 
#               'version': '2',
#               'action': encoded_action}

    # Right now, current does not support this api. Its safe to return
    # an empty dict.
    result = {}
    return {'type': 'xml',
            'data': result}


def submit(sysid_string, action_id, status, message, data):
    """ Get a response back from the client for a particular action_id. """

    logfunc(locals())

    # Authorize the client
    si = auth.SysId()
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")
 
    result = 0
    # The return value is ignored, so I can't figure out the return _type_.
    # We assume 0 is safe.
    return {'type': 'xml',
            'data': result}


## END OF LINE ##
