""" Implement the administrative api calls for current itself.

Notice that these API calls have nothing to do with up2date or RHN - they
are purely an invention of current.

Copyright 2002 Hunter Matthews

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

"""

import xmlrpclib
import string
import pprint

from logger import *
import auth
import config

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'hello',
    ]


def hello(first, second):
    """ test api call """

    logfunc(locals())

    # Authorize the client
#     si = auth.SysId()
#     si.loadstring(sysid_string)
#     if not si.isValid():
#         return xmlrpclib.Fault(1000, "Invalid client certificate.")

    # We do nothing except hand our args back in a pretty string.
    return "hello world! welcome from %s and %s" % (first, second)


## END OF LINE ##
