""" A single "virtual" interface for all the storage needs.

The api modules (up2date, errata, etc) make calls into the CurrentDB - the
api modules have no knowledge of the storage method itself. Conversely,
CurrentDB knows nothing of xmlrpc, GET methods, or other delusions.

This file provides a "virtual" base class. Its basically the documentation
for what methods each backend class must support.

Copyright (c) 2002 Hunter Matthews    Distributed under GPL.

"""

from logger import *

class CurrentDB:
    """ CurrentDB represents the entire data storage capability for 
    current.

    This "virtual" class declares the required API and some universal 
    helper functions.

    """

    def __init__(self):
        """ Create a database object. """
        pass


    def initdb(self, config):
        """ Create a new database.
    
        Called by the cinstall program, ONCE, per database.

        Config should be a dictionary of required keys (or something
        that acts like a dictionary).
        """
        
        # create the web dir, which is used by ALL the backends 
        # side effect is to create the current dir if it doesn't exist
        web_dir = os.path.join(config['current_dir'], 'www')
        os.system("mkdir -p %s" % web_dir)







## END OF LINE ##
