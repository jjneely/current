from current.admin import CadminConfig
import pprint
import sys

class Module(CadminConfig):

    shortHelp = "Unsubscribe a system to a channel."

    def run(self, server, argv):
        usage = "usage: %prog unsubscribe -u <uuid> -l <label>"
        parser = self.defaultParser(usage)
        (opts, leftargs) = parser.parse_args(argv)
       
        if len(opts.uuid) != 1 or len(opts.channels) != 1:
            parser.print_help()
            sys.exit(1)

        uuid = opts.uuid[0]
        label = opts.channels[0]
       
        result = self.call(server.cadmin.unsubscribe, uuid, label)
        pprint.pprint(result)
    
    def name(self):
        return "unsubscribe"

