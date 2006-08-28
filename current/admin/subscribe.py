from current.admin import CadminConfig
import pprint
import sys

class Module(CadminConfig):

    shortHelp = "Subscribe a system to a channel."

    def run(self, server, session, argv):
        usage = "usage: %prog subscribe -u <uuid> -l <label>"
        parser = self.defaultParser(usage)
        (opts, leftargs) = parser.parse_args(argv)
       
        if len(opts.uuid) != 1 or len(opts.channels) != 1:
            parser.print_help()
            sys.exit(1)

        uuid = opts.uuid[0]
        label = opts.channels[0]
       
        result = self.call(server.cadmin.subscribe, uuid, label)
        pprint.pprint(result)
    
    def name(self):
        return "subscribe"

