""" Up2date registration API module.

Copyright (c) 2001 Hunter Matthews    Distributed under GPL.

For details on the exact API, what each method expects and what it 
returns, please see the rhn_api.txt file.

"""

import xmlrpclib
import rpm 
import pprint

from current.exception import *
from current import auth
from current import configure
from current import profiles
from current import users
from current.logger import *


# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'welcome_message',
    'privacy_statement',
    'terms_and_conditions',
    'reserve_user',
    'register_product',
    'new_user',
    'new_system',
    'send_serial',
    'add_hw_profile',
    'refresh_hw_profile',
    'add_packages',
    'delete_packages',
    'update_packages',
    'list_packages', 
    'upgrade_version',
    'update_transactions',
    ]


def welcome_message():
    return configure.config['welcome_message']
    

def privacy_statement():
    return configure.config['privacy_statement']


def terms_and_conditions():
    # return config.cfg.getItem("terms_and_conditions")
    return ""


def reserve_user(username, password):

    try:
        u = users.Users(username)
    except CurrentException, e:
        return xmlrpclib.False

    if u.isValid(password):
        return xmlrpclib.True
    else:
        return xmlrpclib.False


def new_user(username, password, email_address=None,
             org_id=None, org_password=None):
    # org_id and org_password only in 2.7+

    # Some limit checks
    if len(password)<5:
        return xmlrpclib.Fault(14, 'Password too short')
    if len(username)<5:
        return xmlrpclib.Fault(15, 'Username too short')

    # see if the user exits. If so, do nothing if passwd match
    try:
        u = users.Users(username)
        if u.isValid(password):
            return 0
        else:
	    return xmlrpclib.Fault(3, 'User exists, but password mismatch')
    except CurrentException, e:
        pass

    u = users.Users()
    u.newUser(username, password)
    return 0
    
            
def new_system(system_dict, packages=None):

    # FIXME: Currently we generate a sysid as similar as possible to the 
    # RHN up2date server. But we don't need to - what is operating_system
    # or 'type' to us? Should we pare this down to what current needs?
    si = auth.SysId()

    # Authenticate request.  system_dict with either contain a username and
    # password fields OR a "token" field that will contain the activationkey

    try:
        u = users.Users(system_dict['username'])
    except CurrentException, e:
        return xmlrpclib.False
    if not u.isValid(system_dict['password']):
        return xmlrpclib.False

    # Create Profile
    p = profiles.Profile()

    # XXX: Reactivation of old profile with matching uuid?
    p.newProfile(u.pid,
                 system_dict['architecture'], system_dict['os_release'],
                 system_dict['profile_name'], system_dict['release_name'],
                 system_dict['rhnuuid'])

    # Copy all the relevant fields out of system_dict
    for attr in ['username', 'profile_name', 'architecture', 'os_release' ]:
        si.setattr(attr, system_dict[attr])

    # Add the fields strictly from the server side
    si.setattr('type', 'REAL')
    si.setattr('checksum', '')   # dumpstring sets final value for this

    # The system_id is a little different than what RHN does. Use the uuid.
    si.setattr('system_id', p.uuid)
    si.setattr('operating_system', 'Red Hat Linux')
    si.setattr('description', 
               '%(os_release)s running on %(architecture)s' % system_dict)

    return si.dumpstring()

    
def register_product(sysid_string, product_info):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    return 0
    
            
def send_serial(sysid_string, serial_number, oemid=None):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    return 0
    

def add_hw_profile(sysid_string, hardware_info):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    return 0
    
    
def refresh_hw_profile(sysid_string, hardware_info):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    return 0
    
    
def add_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")

    subscribedChans = p.getChannels()
    first = 1
    for (pkg) in package_list:
        if first:
            try:
	        (name,version,release,epoch,arch,cookie) = pkg
	    except Exception, e:
		first = 0
	        (name,version,release,epoch) = pkg
	else:
	    (name,version,release,epoch) = pkg

	p.addPackage(subscribedChans,name,version,release,epoch)
    return 0

    
def delete_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")

    for (pkg) in package_list:
	(name,version,release,epoch) = pkg
	p.deletePackage(name,version,release,epoch)
    return 0

    
def update_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # Get client's profile
    try:
        p = profiles.Profile(si.getattr('system_id'))
    except CurrentException, e:
        log("Fault! Sysid does not refer to a valid profile", VERBOSE)
        log("Error: %s" % str(e), VERBOSE)
        return xmlrpclib.Fault(1000, "Invalid system credentials.")

    #clear out the current list of packages and re-add them
    subscribedChans = p.getChannels()
    p.deletePackage(None)
    for (pkg) in package_list:
	(name,version,release,epoch) = pkg
	p.addPackage(subscribedChans,name,version,release,epoch)
    return 0

    
def list_packages(sysid_string):
    """ This function is still included, but apparently not used. """

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # we don't know what format the client is expecting...
    return "no information"

    
def update_transactions(sysid_string, time, transaction_data):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    return 0

    
def upgrade_version(sysid_string, new_os_release):

    # Authorize the client
    si = auth.SysId(sysid_string)   
    (valid, reason) = si.isValid()
    if not valid:
        return xmlrpclib.Fault(1000, reason)

    # Make a new sysid from the old one. Yes, we parse the sysid twice here.
    new_sysid = auth.SysId()
    new_sysid.loadstring(sysid_string)
    
    new_sysid.setattr('os_release', new_os_release)

    return new_sysid.dumpstring()

## END OF LINE ##    
