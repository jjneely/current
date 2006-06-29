from current.admin import CadminConfig
from current import xmlrpc
import pprint
import optparse
import sys

class Module(CadminConfig):

    shortHelp = "Add a directory of packages to a channel."

    def run(self, server, argv):
        u = "usage: %prog add_dir <channel> <dir> [[dir] ...]"
        parser = optparse.OptionParser(u)
        parser.add_option("-l", "--label", action="store", 
                          type="string", dest="chanlabel")
        parser.add_option("-d", "--dir", action="append", 
                          type="string", dest="dirs")
        (opts, leftargs) = parser.parse_args(argv)


        chan = {}
        if opts.chanlabel != None:
            chan['label'] = opts.chanlabel
        elif len(leftargs) > 0:
            chan['label'] = leftargs[0]
        else:
            parser.print_help()
            sys.exit()

        if opts.dirs != None:
            chan['dirs'] = opts.dirs
        elif len(leftargs) > 1 and opts.chanlabel == None:
            chan['dirs'] = leftargs[1:]
        elif len(leftargs) > 0 and opts.chanlabel != None:
            chan['dirs'] = leftargs
        else:
            parser.print_help()
            sys.exit()
            
        result = xmlrpc.doCall(server.cadmin.addChannelPath, chan)
        pprint.pprint(result)

