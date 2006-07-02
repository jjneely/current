from current.admin import CadminConfig
from current import xmlrpc
import pprint
import sys

class Module(CadminConfig):

    shortHelp = "Find UUIDs from profile names."

    def run(self, server, argv):
        usage = "usage: %prog search"
        if len(argv) is not 0:
            print usage
            sys.exit(1)
            
        result = xmlrpc.doCall(server.cadmin.findProfile)
        pprint.pprint(result)
    
    def name(self):
        return "search"

