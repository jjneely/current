from admin import CadminConfig, rpcServer
import pprint

class Module(CadminConfig):

    shortHelp = "Test connection to Current server."

    def run(self, server, argv):
        result = rpcServer.doCall(server.cadmin.status)
        pprint.pprint(result)
    
    def name(self):
        return "test"

