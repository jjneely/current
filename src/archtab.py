""" Internal module to handle all things arch related. 

Ideally we'd just query rpm for various bits of this kind of info. 
However, there are no mechanisms available to us for use on a _server_ 
that may have a different arch than a client. So, we reinvent the wheel.

Copyright 2002 Hunter Matthews

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

The compat_arches_table and related functions are from the up2dateUtils.py
file from RH's up2date client. That files copyright info follows:

 Client code for Update Agent
 Copyright (c) 1999-2001 Red Hat, Inc.  Distributed under GPL.

 Author: Preston Brown <pbrown@redhat.com>
         Adrian Likins <alikins@redhat.com>


"""

from logger import *


def getCannonArch(arch):
    """ Translate an arch into its base platform name.

     For example, a i686's base arch is i386
    """

    logfunc(locals())

    # BUGFIX: In newer versions of up2date (first seen in RHEL 3) the
    # client isn't sending us a simple arch "i686" but the contents of
    # the /etc/rpm/platform file e.g. "i386-redhat-linux"
    # We assume that we can split off of '-'s and take the first element.
    arch = arch.split('-')[0]
    
    assert arch in _compat_arches_table.keys(), \
        "Arch table does not contain %s architecture." % arch
    return _compat_arches_table[arch][0]


# NOTE: The order of the stuff in compat is in newest->oldest order
# assuming backwards compability
# I think there is a bug in rpm, in that althon's should not use i686 
# kernels, however, thats what we are duplicating, so thats whats in 
# the table.
_compat_arches_table = {
    # ARCH      : # CANON,      # COMPAT
    "noarch"    : [ "noarch",   "noarch" ],

    "i386"      : [ "i386",     "i386", "noarch" ],
    "i486"      : [ "i386",     "i486", "i386", "noarch" ],
    "i586"      : [ "i386",     "i586", "i486", "i386", "noarch" ],
    "i686"      : [ "i386",     "i686", "i586", "i486", "i386", "noarch" ],
    "athlon"    : [ "i386",     "athlon", "i686", "i586", "i486", "i386", "noarch" ],

    "alpha"     : [ "alpha",    "alpha", "noarch" ],
    "alphaev5"  : [ "alpha",    "alphaev5", "alpha", "noarch" ],
    "alphaev56" : [ "alpha",    "alphaev56", "alphaev5", "alpha", "noarch" ],
    "alphaca56" : [ "alpha",    "alphaca56", "alphaev56", "alphaev5", "alpha", "noarch" ],
    "alphaev6"  : [ "alpha",    "alphaev6", "alphaca56", "alphaev56", "alphaev5", "alpha", "noarch" ],
    "alphaev67" : [ "alpha",    "alphaev67", "alphaev6", "alphaca56", "alphaev56", "alphaev5", "alpha", "noarch" ],

    "sparc"     : [ "sparc",    "sparc", "noarch" ],
    "sparcv9"   : [ "sparc",    "sparcv9", "sparc", "noarch" ],
    "sparc64"   : [ "sparc",    "sparc64", "sparcv9", "sparc", "noarch" ],

    "ia64"      : [ "ia64",     "ia64", "i686", "noarch" ],

    "x86_64"    : [ "x86_64",   "noarch" ],

    "src"       : [ "SRPMS",    "src" ],
    }
    
    
