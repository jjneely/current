from current.admin import CadminConfig
import pprint
import sys
import optparse

class Module(CadminConfig):

    shortHelp = "List Profile Information"

    def run(self, server, session, argv):
        usage = "usage: %prog search [-p Profile ID]"
        parser = optparse.OptionParser(usage)
        parser.add_option("-p", "--profileid", action="store", 
                          type="int", dest="pid", default=None)
        (opts, leftargs) = parser.parse_args(argv)
        
        if opts.pid:
            result = self.call(server.cadmin.findProfile, session, opts.pid)
        else:
            result = self.call(server.cadmin.findProfile, session)
            
        pprint.pprint(result)
    
    def name(self):
        return "search"

