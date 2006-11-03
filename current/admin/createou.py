from current.admin import CadminConfig
from current import xmlrpc
from types import IntType
import pprint
import logging
import sys
import optparse

logger = logging.getLogger()
log = logger.log

class Module(CadminConfig):

    shortHelp = "Create a new OU."

    def run(self, server, session, argv):
        u = "%prog createou -p <parent OU ID> -l <OU Label> [-d <Description>]"
        parser = optparse.OptionParser(u)
        parser.add_option("-p", "--parent", action="store", type="int", 
                          dest="parent", default=None)
        parser.add_option("-l", "--label", action="store", type="string", 
                          dest="label", default=None)
        parser.add_option("-d", "--description", action="store", type="string",
                          dest="desc", default="")
        (opts, leftargs) = parser.parse_args(argv)
        
        if opts.parent == None or opts.label == None:
            parser.print_help()
            sys.exit()

        result = xmlrpc.doCall(server.policy.createOU, session, 
                               opts.parent,
                               opts.label,
                               opts.desc)
        if isinstance(result, IntType):
            print "Created OU ID %s." % result

        return result
    

