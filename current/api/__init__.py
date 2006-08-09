"""The api package implements the xmlrpc calls that current understands.
    
up2date, rhn_register, and cadmin make xmlrpc calls to the api package.

Copyright 2001, 2002 Hunter Matthews

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

See http://www.biology.duke.edu/computer/unix/current
"""

from current.api import cadmin
from current.api import errata
from current.api import queue
from current.api import registration
from current.api import up2date
from current.api import applet
from current.api import yum
from current.api import systems
from current.api import channels

## END OF LINE ##

