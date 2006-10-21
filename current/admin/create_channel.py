from current.admin import CadminConfig
from current import xmlrpc
import pprint
import logging
import sys
import optparse

logger = logging.getLogger()
log = logger.log

class Module(CadminConfig):

    shortHelp = "Create a channel or subchannel."

    def run(self, server, session, argv):
        u = "%prog create_channel -l <label> -a <arch> -r " \
                "<release> -n <name> [options]"
        parser = optparse.OptionParser(u)
        parser.add_option("-n", "--name", action="store", type="string", 
                          dest="channelname")
        parser.add_option("-l", "--label", action="store", type="string", 
                          dest="channellabel")
        parser.add_option("-a", "--arch", action="store", type="string", 
                          dest="channelarch")
        parser.add_option("-r", "--release", action="store", type="string", 
                          dest="channelrelease")
        parser.add_option("-p", "--parent", action="store", type="string", 
                          dest="channelparent")
        parser.add_option("-d", "--description", action="store", type="string",
                          dest="channeldesc", default="")
        parser.add_option("-b", "--base", action="store_true",
                          dest="base", default=False)
        (opts, leftargs) = parser.parse_args(argv)
        
        if len(leftargs) != 0:
            parser.print_help()
            sys.exit()
            
        chan = {}
        if opts.channelname and opts.channellabel:
            chan['name'] = opts.channelname
            chan['label'] = opts.channellabel
        else:
            parser.print_help()
            sys.exit()

        chan['desc'] = str(opts.channeldesc)
        chan['base'] = opts.base

        if opts.channelparent:
            log(1, "Sub-Channels are not yet supported.")
            sys.exit(1)
            chan['parent'] = opts.channelparent
        else:
            if opts.channelarch and opts.channelrelease:
                chan['arch'] = opts.channelarch
                chan['release'] = opts.channelrelease
            else:
                parser.print_help()
                sys.exit()
    
        result = xmlrpc.doCall(server.cadmin.createChannel, session, chan)
        pprint.pprint(result)
    

