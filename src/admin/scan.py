from admin import CadminConfig
import xmlrpc
import pprint
import optparse
import sys

class Module(CadminConfig):

    shortHelp = "Update all packages from disk for the given channels."

    def run(self, server, argv):
        u = "usage: %prog scan <channel> [[channel] ...]"
        parser = optparse.OptionParser(u)
        parser.add_option("-l", "--label", action="append", 
                          type="string", dest="channels")
        (opts, leftargs) = parser.parse_args(argv)
        
        if opts.channels == None:
            oChans = []
        else:
            oChans = opts.channels

        if len(leftargs) == 0 and len(oChans) == 0:
            parser.print_help()
            sys.exit()

        chan = {}
        chan['channels'] = oChans + leftargs
        result = xmlrpc.doCall(server.cadmin.scanChannels, chan)
        pprint.pprint(result)

