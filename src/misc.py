## misc.py
##
## misc helper functions for implementing the server side of 
##   up2date/rhn_register
##
## Copyright (c) 2001 Hunter Matthews    Distributed under GPL.
##

import xmlrpclib
import pprint
import rpm
import string
import os 


# This should not be necessary, but os.path.join() does NOT do what we
# want.
def PathJoin(*components):
    ret = components[0]
    components = components[1:]
    for path in components:
        ret = ret + "/" + path 
    return ret
                        

## END OF LINE ##    
 
