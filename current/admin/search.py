from current.admin import CadminConfig
import pprint
import sys

class Module(CadminConfig):

    shortHelp = "Find UUIDs from profile names."

    def run(self, server, session, argv):
        usage = "usage: %prog search"
        if len(argv) != 0:
            print usage
            sys.exit(1)
            
        result = self.call(server.cadmin.findProfile, session)
        pprint.pprint(result)
    
    def name(self):
        return "search"

