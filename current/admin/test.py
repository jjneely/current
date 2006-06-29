from current.admin import CadminConfig
from current import xmlrpc
import pprint

class Module(CadminConfig):

    shortHelp = "Test connection to Current server."

    def run(self, server, argv):
        result = xmlrpc.doCall(server.cadmin.status)
        pprint.pprint(result)
    
    def name(self):
        return "test"

