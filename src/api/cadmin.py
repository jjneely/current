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

from logger import *
import auth
import configure

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'status',
    ]


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
