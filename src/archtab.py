""" Internal module to handle all things arch related. 

Ideally we'd just query rpm for various bits of this kind of info. 
However, there are no mechanisms available to us for use on a _server_ 
that may have a different arch than a client. So, we reinvent the wheel.

Copyright 2002, 2005 Hunter Matthews and Jack Neely

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

Parts of the code taken from archwork.py in Yum Copyright 2002 Duke University.

"""

import os
import re

from current.logger import *

def getArch(arch=None):
    if not arch:
        arch = os.uname()[4]
    newarch = None
    if re.search('86', arch):
        newarch = 'i386'
    if re.search('sparc', arch) or re.search('sun', arch):
        newarch = 'sparc'
    if re.search('alpha', arch):
        newarch = 'alpha'
    if re.search('ppc', arch):
        newarch = 'ppc'
    if re.search('x86_64', arch):
        newarch = 'x86_64'
    if not newarch:
        newarch = arch
    return newarch

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
    
    return getArch(arch)

