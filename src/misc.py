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
from logger import *

# NOTE: The order of the stuff in compat is in newest->latest order
# assuming backwards compability
_compat_arches_table = {
    # ARCH      : # CANON,      # COMPAT
    "noarch"    : [ "noarch",   "noarch" ],
    "i386"      : [ "i386",     "i386", "noarch" ],
    "i486"      : [ "i386",     "i486", "i386", "noarch" ],
    "i586"      : [ "i386",     "i586", "i486", "i386", "noarch" ],
    "i686"      : [ "i386",     "i686", "i586", "i486", "i386", "noarch" ],
    "athlon"    : [ "i386",     "athlon", "i686", "i586", "i486", "i386", "noarch" ],
    "alpha"     : [ "alpha",    "alpha", "noarch" ],
    "alphaev6"  : [ "alpha",    "alphaev6", "alpha", "noarch" ],
    "sparc"     : [ "sparc",    "sparc", "noarch" ],
    "sparcv9"   : [ "sparc",    "sparcv9", "sparc", "noarch" ],
    "sparc64"   : [ "sparc",    "sparc64", "sparc", "noarch" ],
    "ia64"      : [ "ia64",     "ia64", "noarch" ],
    "src"       : [ "SRPMS",    "src" ],
    }


# translate an arch into its basename platform name
def _getCannonArch(arch):
    logfunc(locals())

    # XXX: this should not be really happening
    if not arch in _compat_arches_table.keys():
        log("ERROR: Can not locate architecture in internal database",
            MANDATORY)
        log("Looking for %s in %s\n" % (arch, repr(_compat_arches_table)),
            MANDATORY)
        return None
    log ("returning: %s" % (_compat_arches_table[arch][0],) )
    return _compat_arches_table[arch][0]


# Get a list of compatible cpus
def _getCompatibleArchs(arch):
    logfunc(locals())
    # XXX: this should not be really happening
    if not arch in _compat_arches_table.keys():
        log("ERROR: Can not locate architecture in internal database",
            MANDATORY)
        log("Looking for %s in %s\n" % (arch, repr(_compat_arches_table)),
            MANDATORY)
        return None
    return _compat_arches_table[arch][1:]



## END OF LINE ##    
 
