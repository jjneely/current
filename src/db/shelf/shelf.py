""" Implements the current database backend as python shelves. """

import operator
import os
import string
import shelve

import misc
import channel
from logger import *
from db.currentdb import CurrentDB


class ShelfDB(CurrentDB):
    """ Implements CurrentDB (at least the rpm parts) as python shelves.

    This backend is ickier than the others, but is older and better
    understood, for now. Do not expect this backend to survive - it 
    simply cannot scale up to meet all of currents needs.
    """
    
    def __init__(self):
        self.channels = {}
        self.index = {}


    def initdb(self, config):
        """ Do the steps necessary to create an empty database.

        This should be enough to get the mod_python module working.
        """
    
        # call the parent FIRST
        currentdb.CurrentDB.initdb(self, config)

        # We steal a dir off the main current dir for our databases.
        # we'll have one main pickle/shelf for the whole thing, and then
        # one dir + shelves per channel.
        db_dir = os.path.join(config['current_dir'], 'db')  
        os.system('mkdir -p %s' % db_dir)

        c_shelve = shelve.open(os.path.join(db_dir, 'current.wdb'))
        for key in ['log_file', 'apache_config_file', 'current_dir',
                    'access_type', 'access_arg']:
            x = config[key]  
            c_shelve[key] = x
        c_shelve.close()
        

    def connect(self):
        # This routine does diddly with shelves, but it's needed for API
        # compatibility.
        pass


    # loadChannels() does what the main current() file used to do, but it's
    # actually back-end specific.
    def loadChannels(self, config):
        for chan in config.config['valid_channels']:
            db_dir = config.config['channels'][chan]['db_dir']
            try:
                log("Adding channel '%s' in dir %s" % (chan, db_dir), DEBUG)
                self.addChannel(db_dir)
            except:
                log("Error opening channel '%s'" % chan, MANDATORY)
                log("Shutting down because we could not start the server",
                    MANDATORY)
                
                sys.exit(1)

    def addChannel(self, chan_info):
        # Everything we need to know about the channel is kept in a 
        # channel object. Just instantiate and read in the new channel.

        tmp = shelf_channel.Channel()        
        tmp.open(chan_info, 'r')

        new_label = tmp.chanInfo['label']
        new_arch = tmp.chanInfo['arch']
        new_rel = tmp.chanInfo['os_release']

        # Add channel object itself
        self.channels[new_label] = tmp

        # Now add that chan to our EasyBake(tm) lookup index
        if self.index.has_key(new_arch):
            if self.index[new_arch].has_key(new_rel):
                log ("Cannot have two channels with same property.", TRACE)
                raise Exception('Cannot have two chans with same properties')
            else:
                self.index[new_arch][new_rel] = new_label
        else:
            self.index[new_arch] = {}
            self.index[new_arch][new_rel] = new_label


    def getCompatibleChannels(self, client_arch, client_release):
        """ Scan our channel collections for ones that will work for this
        client.

        We return a list of 'chanInfo' dict's. 

        """

        logfunc(locals())

        # determine the clients cannonical arch
        cannon = self._getCannonArch(client_arch)
        log ("Canon arch found: %s" % cannon, DEBUG)

        # FIXME: Right now, we assume only one channel will match.
        # see if we have a match for a [cannon][os_release] pair
        # what keys do we have?
        if self.index.has_key(cannon):
            if self.index[cannon].has_key(client_release):
                label = self.index[cannon][client_release]
            else:
                # Have that cannonical arch, but not that release
                log ("We know the arch, but not the release", TRACE)
                return []
        else:
            # We don't server that arch, at any release level
            log("We don't know the arch!", TRACE)
            return []
        
        return [self.channels[label].chanInfo]


    def getPackageList(self, chan_label, chan_version):
        """ Get the list of packages for a particular channel. 

        This method is a little strange, as the output is already xmlrpc
        formatted for us. 

        FIXME: This really needs to do something intelligent with the 
        version.

        """

        logfunc(locals())

        list_filename = self.channels[chan_label].getPackageListCache()
        log('List filename being returned: %s' % list_filename, DEBUG2)

        return list_filename
 

    def solveDependancy(self, chan_label, client_arch, unknown):
        logfunc(locals())

        # This call will not fail - it'll return None if nothing found.
        pick_list = self.channels[chan_label].getDependancy(unknown)

        return pick_list


    def getPackageFilename(self, chan_label, package):
        """ Get the filename for a particular rpm. """

        logfunc(locals())

        return self.channels[chan_label].getRpmFilename(package)
            

    def getPackageHeaderFilename(self, chan_label, header_name):

        logfunc(locals())
 
        return self.channels[chan_label].getPackageHeaderCache(header_name)

        
    def getSrcPackageFilename(self, chan_label, package):
        """ Get the filename for a particular source rpm. 

        This ones nice - we get a string, look it up in a dict, return.

        """
    
        # FIXME: This could fail.
        current_pick = self.channels[chan_label].getSrcRpmFilename(package)

        return current_pick
            

## END OF LINE ##
