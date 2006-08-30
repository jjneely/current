from current.admin import CadminConfig
import pprint
import sys
import getpass

class Module(CadminConfig):

    shortHelp = "Authenticate to a Current server."

    def run(self, server, session, argv):
        usage = "usage: %prog login"

        sys.stdout.write("Login: ")
        user = sys.stdin.readline().strip()
        password = getpass.getpass("Password:")

        result = self.call(server.cadmin.login, user, password)
        if result['code'] == 0:
            print "Login successful."
            return result['session']
        elif result['code'] == 1:
            print "Initial account created.  You are super user."
            return result['session']
        elif result['code'] == -1:
            print "Login failed.  Check your username and password."
        else:
            print "An undefined error has occured."

        return ""
    
    def name(self):
        return "login"

