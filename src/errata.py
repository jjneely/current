# errata.py

""" Up2date errata API module.

Copyright (c) 2001 Hunter Matthews    Distributed under GPL.

For details on the exact API, what each method expects and what it 
returns, please see the rhn_api.txt file.

"""

import xmlrpclib
import rpm 
import pprint

import misc
import auth
from logger import *


# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'getPackageErratum',
    ]



def getPackageErratum(sysid_string, pkg):
    """ Get the errata annoucement for a particular package. 

    It would be neat to somehow capture the errata annoucements in
    foo-1.0-1.*.txt and blast that back to client, and respond with
    something bland for the rest, but thats left as a later task.

    """

    logfunc(locals())

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    advisory = [{
        "errata_type": "unknown",
        "advisory":    " ",
        "topic":       pkg[0],
        "description": "No details about this package are available. Sorry."
        }]

    return {'type': 'xml',
            'data': advisory}
        

## END OF LINE ##    

