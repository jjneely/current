""" Up2date errata API module.

Copyright (c) 2003 Hunter Matthews    Distributed under GPL.

For details on the exact API, what each method expects and what it returns,
please see the rhn_api.txt file.

"""

import xmlrpclib
import rpm 
import pprint

import auth
from logger import *


# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'getPackageErratum',
    'GetByPackage',
    ]



def getPackageErratum(sysid_string, pkg):
    """ Get the errata annoucement for a particular package. 

    It would be neat to somehow capture the errata annoucements in
    foo-1.0-1.*.txt and blast that back to client, and respond with
    something bland for the rest, but thats left as a later task.

    """

    logfunc(locals())

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    advisory = {
        "errata_type": "unknown",
        "advisory":    " ",
        "topic":       pkg[0],
        "description": "No details about this package are available. Sorry."
        }

    return [advisory,]
        

def GetByPackage(pkg_name, os_release):
    """ Get the errata annoucement for a particular package. """

    logfunc(locals())

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    advisory = {
        "errata_type": "unknown",
        "advisory":    " ",
        "topic":       pkg[0],
        "description": "No details about this package are available. Sorry.",
        "errata_id": "0",
        "synopsis": " ",
        }

    return [advisory,]

## END OF LINE ##    

