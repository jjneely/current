""" Implement the administrative api calls for current itself.

Notice that these API calls have nothing to do with up2date or RHN - they
are purely an invention of current.

Copyright 2002, 2006 Hunter Matthews, Jack Neely

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

"""

import sys
import xmlrpclib

from current.logger import *
from current.exception import *
from current.users import SessionUser, User
from current.ou import OU

# Failed Auth error code
EAUTH = 17

# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'login',
    'createUser',
    'showTree',
    'createOU',
    ]

def login(username, password):
    # This is over SSL, right?  RIGHT?

    u = SessionUser()
    sessid = u.login(username, password)

    # sessid a coded tuple for us
    return sessid

def createUser(sess, username, password, ou, email):
    # SSL, right?
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    new = User()
    new.newUser(username, password, ou, email)
    # Will raise exception if username already exists.
    return True

def showTree(sess):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    oulib = OU()
    return oulib.showTree()

def createOU(sess, parent, label, description):
    u = SessionUser(sess)
    if not u.isValid():
        return xmlrpclib.Fault(EAUTH, "Bad session.  Please login.")

    oulib = OU()
    return oulib.createOU(parent, label, description)

## END OF LINE ##
