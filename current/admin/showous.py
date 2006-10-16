from current.admin import CadminConfig
import pprint

class Module(CadminConfig):

    shortHelp = "Display the OU tree."

    def display(self, list):
        print "OU ID\t|Label"
        print "================"

        for row in list:
            print "%s\t|%s%s" % (row['ou_id'],
                                " "*2*row['depth'],
                                row['label'])

    def run(self, server, session, argv):
        usage = "usage: %prog showou"

        result = self.call(server.cadmin.showTree, session)

        self.display(result)

        return True
    
    def name(self):
        return "createuser"

