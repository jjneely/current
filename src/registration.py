# registration.py

""" Up2date registration API module.

Copyright (c) 2001 Hunter Matthews    Distributed under GPL.

For details on the exact API, what each method expects and what it 
returns, please see the rhn_api.txt file.

"""

import xmlrpclib
import rpm 
import pprint

import misc
import auth
import config
from logger import *


# Special array of exported functionality. 
# Idea stolen from up2date/getMethod.py
__current_api__ = [
    'welcome_message',
    'privacy_statement',
    'reserve_user',
    'register_product',
    'new_user',
    'new_system',
    'send_serial',
    'add_hw_profile',
    'add_packages',
    'delete_packages',
    'update_packages',
    'upgrade_version',
    ]


def welcome_message():
    return {'type': 'xml',
            'data': config.cfg.getItem("welcome_message")}
    

def privacy_statement():
    return {'type': 'xml',
            'data': config.cfg.getItem("privacy_statement")}


def reserve_user(username, password):
    return {'type': 'xml',
            'data': xmlrpclib.False}


def new_user(username, password, email_address=None,
             org_id=None, org_password=None):
    # org_id and org_password only in 2.7+
    return {'type': 'xml',
            'data': 0}
    
            
def new_system(system_dict, packages=None):

    # FIXME: Currently we generate a sysid as similar as possible to the 
    # RHN up2date server. But we don't need to - what is operating_system
    # or 'type' to us? Should we pare this down to what current needs?
    si = auth.SysId()

    # Copy all the relevant fields out of system_dict
    for attr in ['username', 'profile_name', 'architecture', 'os_release' ]:
        si.setattr(attr, system_dict[attr])

    # Add the fields strictly from the server side
    si.setattr('type', 'REAL')
    si.setattr('checksum', '')
    si.setattr('system_id', 'Current-ANONYMOUS')
    si.setattr('operating_system', 'Red Hat Linux')
    si.setattr('description', 
               '%(os_release)s running on %(architecture)s' % system_dict)

    return {'type': 'xml',
            'data': si.dumpstring()}

    
def register_product(sysid_string, product_info):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}
    
            
def send_serial(sysid_string, serial_number, oemid=None):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}
    

def add_hw_profile(sysid_string, hardware_info):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}
    
    
def add_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}
    
    
def delete_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}

    
def update_packages(sysid_string, package_list):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    return {'type': 'xml',
            'data': 0}

    
def upgrade_version(sysid_string, new_os_release):

    # Authorize the client
    si = auth.SysId()   
    si.loadstring(sysid_string)
    if not si.isValid():
        return xmlrpclib.Fault(1000, "Invalid client certificate.")

    # Make a new sysid from the old one. Yes, we parse the sysid twice here.
    new_sysid = auth.SysId()
    new_sysid.loadstring(sysid_string)
    
    new_sysid.setattr('os_release', new_os_release)

    return {'type': 'xml',
            'data': new_sysid.dumpstring()}

## END OF LINE ##    
