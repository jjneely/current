## auth.py
""" Authentication and Authorization module for current.

For authentication, we have SysId and SysHeader objects that try to say who
and what a client is. For authorization, we have the Authorization object.

Copyright (c) 2001 Hunter Matthews    Distributed under GPL.

"""

import xmlrpclib
import pprint
import string
import sha
import time

import configure
import ConstructParser
from logger import *

# Program global authorization object setup by main().
authorize = None


class SysId:
    """ Individual client hosts are identified by a sysid structure.

    This object manages, creates new sysid's and provides access to 
    existing ones.

    """

    # NOTE: 'fields' is left out of this list - we generate that
    # automagically, instead of letting the user set it.
    _attr_list = ['type', 'checksum', 'description', 'system_id', 
                  'operating_system', 'os_release', 'architecture',
                  'profile_name', 'username']


    def __init__(self, sysid_string=None):
        self._data = {}
        if sysid_string:    
            self.loadstring(sysid_string)


    def loadstring(self, xmlstring):
        """ xmlstring should be the xml encoded systemid from the client."""
        
        # xmlstring has no method name, but loads always returns one ....
        (args, method_name) = xmlrpclib.loads(xmlstring)
        self._data = args[0]


    def dumpstring(self):
        """ Creates a new xml encoded string from this object.

        Used for new/changed clients.
        The format is a tuple of a list of a dict. I don't know why.
        """
        
        # Make a shallow copy for adding 'fields' to.
        self.setChecksum()
        tmp = self._data.copy()
        tmp['fields'] = self._data.keys()
        return '<?xml version="1.0"?>\n' + \
               xmlrpclib.dumps(tuple([tmp]))        


    def setattr(self, attr, value):
        if attr in SysId._attr_list:
            self._data[attr] = value
        else:
            raise Exception("Invalid attribute for sysid")


    def getattr(self, attr):
        if attr in SysId._attr_list:
            return self._data[attr]
        else:
            raise Exception("Invalid attribute for sysid")


    def dump(self):
        return pprint.pformat(self._data)

    
    def _calcChecksum(self):
        """ Calculate the checksum field of the system id. """
        
        str = configure.config['server_secret']
        for attr in ["system_id", "os_release", "architecture", 
                     "profile_name", "username" ]:
            str = str + self._data[attr] 
        
        sum = sha.new(str)
        return sum.hexdigest()
                    

    def setChecksum(self):
        """ Calculate the checksum field of the system id. """
        
        self._data['checksum'] = self._calcChecksum()
                    

    def isValid(self):
        """ Verify that this "structure" of xml has the right format to
        be a systemId. This says nothing about where it's authorized or not.

        """

        # Check for all required fields        
        for attr in ['type', 'checksum', 'description', 'system_id', 
                     'operating_system', 'os_release', 'architecture',
                     'profile_name', 'username']:
            if not self._data.has_key(attr):
                return (0, "Sysid missing required attribute")
        
        # Check that authentication data is unaltered
        sum = self._calcChecksum()
        if self._data['checksum'] != sum:
            return (0, "Sysid checksum is incorrect")

        # Type must be real, as yet I'm not sure what that is.
        if self._data['type'] != 'REAL':
            return (0, "Sysid type is incorrect")

        # We don't support sysid's from other server systems, and
        # we only support anonymous clients. (at the moment).
        system_id = self._data['system_id']
        (server_software, number) = string.split(system_id, '-')
        if server_software != 'Current':
            return (0, "Sysid is from some other server software")

        if number != 'ANONYMOUS':
            return (0, "Sysid does not have a valid system_id number")

        # Everythings ok
        return (1, "Sysid is valid")


class SysHeaders:
    
    def __init__(self, headers=None):
        self.data = {}
        self.data['X-RHN-Server-Id'] = configure.config['server_id']
        self.data['X-RHN-Auth-Channels'] = []

        if headers:
            self.loadHeaders(headers)

        
    def loadSysId(self, si):
        """ Load relevant values from a SysId object into the HeadersId 

        Seems silly to only load one value here, but provides for future 
        expansion.

        """
        
        #si.isValid()        
        self.data['X-RHN-Auth-User-Id'] =  si.getattr('username')
        

    def loadHeaders(self, headers):
        """ Load up a HeadersId object from available 'GET' headers. """

        # The client doesn't seem to send the X-RHN-Client-Version header
        # anymore, so we no longer check for it.
        for attr in ['X-RHN-Auth', 'X-RHN-Auth-Expiration',
                     'X-RHN-Auth-User-Id', 'X-RHN-Server-Id']:

            if not headers.has_key(attr):
                raise Exception("Missing authentication header: %s" % attr)
            else:
                self.data[attr] = headers[attr]

        # We have to handle auth channels as a special case, since for some
        # reason single channel lists are coming back from the client as a 
        # simple list, instead of a list of lists, as was expected.
        attr = 'X-RHN-Auth-Channels'
        if not headers.has_key(attr):
            raise Exception("Missing authentication header: %s" % attr)
        else:
            cp = ConstructParser.ConstructParser(headers[attr])
            try:
                tmpHdr = cp.parseIt()
                log ("Header object successfully parsed: %s" % tmpHdr, DEBUG2)
                if not type(tmpHdr[0]) == type([]):
                    self.data['X-RHN-Auth-Channels'] = [tmpHdr]
                else:
                    self.data['X-RHN-Auth-Channels'] = tmpHdr
            except Exception, e:
                log ("Exception caught: %s" % e, DEBUG2)
                self.data['X-RHN-Auth-Channels'] = ''
            
            # we can't print errors from here effectively, so just making
            # part of the auth data be empty will ensure a neg auth.


    def setTimeValues(self):
        """ Set all the time related fields of the HeadersId. """

        now = int(time.time())

        # FIXME: This should be a config file option, with a default = 3600
        self.data['X-RHN-Auth-Expiration'] = str(now + 3600)


    def addAuthChannel(self, chanInfo):
        """ Append to our authorized channels list. """

        new_chan = [chanInfo['label'], chanInfo['lastupdate']]
        self.data['X-RHN-Auth-Channels'].append(new_chan)        


    def _calcChecksum(self):
        """ Calculate the checksum field of the header id. """
        
        str = configure.config['server_secret']
        for attr in ['X-RHN-Auth-User-Id', 'X-RHN-Server-Id', 
                     'X-RHN-Auth-Expiration']:
            str = str + self.data[attr] 

        # Can't append a list of lists to a string        
        for chan in self.data['X-RHN-Auth-Channels']:
            str = str + chan[0] + ':' + chan[1]

        sum = sha.new(str)
        return sum.hexdigest()
                    

    def setChecksum(self):
        """ Set the checksum field of the header id. """
        
        self.data['X-RHN-Auth'] =  self._calcChecksum()
                    

#     def setattr(self, attr, value):
#         # FIXME: This really needs the valid attribute checking list 
#         #   of sysid, but I don't know what all will be needed yet.
#         self.data[attr] = value
#  
# 
#     def getattr(self, attr):
#         # FIXME: same problem as setattr()
#         return self.data[attr]
 

    def dump(self):
        return pprint.pformat(self.data)

    
    def dumpLoginInfo(self):
        return self.data


    def getAuthChannels(self):
        return self.data['X-RHN-Auth-Channels']
            

    def isValid(self):
        logfunc(locals())

        # Check for required fields
        for attr in ['X-RHN-Auth-User-Id', 'X-RHN-Server-Id', 
                     'X-RHN-Auth-Expiration', 'X-RHN-Auth-Channels']:
            if not self.data.has_key(attr):
                return (0, "SysHeaders missing required attribute")
        
        # Check for server value matching. We won't accept from other
        # people's servers
        if self.data['X-RHN-Server-Id'] != configure.config['server_id']:
            return (0, "SysHeaders from a different server")

        # Client authentication data must be unaltered.
        sum = self._calcChecksum()
        if not self.data['X-RHN-Auth'] == sum:
            return (0, "SysHeaders checksum is incorrect")

        # This can't be all - look for more stuff
        # FIXME: has the expiration gone past?
        # FIXME: do the auth-channels match this actual request?
        # But not in 1.4.1...
        return (1, "SysHeaders are valid")


class Authorization:
    """ Similar to packagedb, a single, program wide object that provides
    authorization services.

    """

    def __init__(self):
        pass

    
    def getAuthorizedChannels(self, sysid, channels):
        """ Return a list of channels a client is allowed to access.

        Arguments are the sysid of the client and a list of channelInfo dicts (from the 
        packagedb). 

        Basically right now we return whatever we get. But in the future,
        STUFF, big important STUFF could happen here.

        I can't wait for someone to tell me what that stuff might be.
        """

        return channels


## END OF LINE ##    
 
