""" Up2date servers API module.

Copyright (c) 2003 Hunter Matthews    Distributed under GPL.

For details on the exact API, what each method expects and what it returns,
please see the rhn_api.txt file.

"""

import xmlrpclib
import pprint

import auth
import config
from logger import *


# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'list',
    ]


def list(sysid_string = None):
    """ Yes, the sysid on this API call is OPTIONAL """

    # Authorize the client, IF we got a sysid string
    if sysid_string:
        si = auth.SysId(sysid_string)   
        (valid, reason) = si.isValid()
        if not valid:
            return xmlrpclib.Fault(1000, reason)

    # we don't have full backend support yet
    # Since the client has "us" configured (otherwise we wouldn't see 
    # this call) then we can just return an empty list.

    return []
    
            
## END OF LINE ##    
