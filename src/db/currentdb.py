""" A single "virtual" interface for all the storage needs.

The api modules (up2date, errata, etc) make calls into the CurrentDB - the
api modules have no knowledge of the storage method itself. Conversely,
CurrentDB knows nothing of xmlrpc, GET methods, or other delusions.

Copyright (c) 2002 Hunter Matthews    Distributed under GPL.

"""

from logger import *

class CurrentDB:
    """ CurrentDB represents the entire data storage capability for 
    current.

    """

## API ##

    def __init__(self, config):
        """ Create a database object. """
        self.config = config


## HELPER FUNCTIONS - NOT PART OF THE CURRENTDB API ##

                    
## END OF LINE ##
                        
