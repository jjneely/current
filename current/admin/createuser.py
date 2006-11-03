from current.admin import CadminConfig
import pprint
import sys
import getpass

class Module(CadminConfig):

    shortHelp = "Create a new user in Current."

    def run(self, server, session, argv):
        usage = "usage: %prog createuser"

        sys.stdout.write("User Name: ")
        user = sys.stdin.readline().strip()
        password1 = getpass.getpass("Password:")
        password2 = getpass.getpass("Password Again:")

        if password1 != password2:
            print "Passwords do not match, try again."
            return None

        sys.stdout.write("OU ID: ")
        ou = sys.stdin.readline().strip()
        sys.stdout.write("Email Address: ")
        email = sys.stdin.readline().strip()

        result = self.call(server.policy.createUser, session, user, 
                           password1, ou, email)
        if result == True:
            print "User created."
        else:
            print "User creation failed."

        return result
    
    def name(self):
        return "createuser"

