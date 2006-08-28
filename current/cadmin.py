#! /usr/bin/python

""" cadmin is the administrative program that performs online tasks.

For now, that consists of creating new channels, adding dirs to 
existing channels, etc.

This software is distributed under the GPL v2, see file "LICENSE"
Copyright 2001, 2002, 2005   Hunter Matthews  <thm@duke.edu> and
Jack Neely <jjneely@gmail.com>

"""

import pprint
import sys
import optparse
import os
import xmlrpclib

# don't import current config - might not be running on a machine
#                               without current.conf
# don't import logger - same reasoning - let's use our own

import logging

log = logging.getLogger("cadmin")
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.INFO)

# Our modules
from current import admin
from current.exception import CurrentRPCError
from current.configure import Preferences # Does this work on machine w/o C

def getServer(url=""):
    if url == "" and not os.access("/etc/sysconfig/rhn/up2date", os.R_OK):
        log.critical("Cannot find a server to contact.")
        sys.exit(1)
    elif url != "":
        server = xmlrpclib.ServerProxy(url)
        return server

    server = admin.rpcServer.getServer()
    try:
        # In 4.2-something-ish this is done in the getServer method
        server.add_trusted_cert(admin.rpcServer.rhns_ca_cert)
    except AttributeError, e:
        pass
    return server


def getArguments():
    # Our syntax is "cadmin [options] COMMAND [options] [args]"  Make it go
    cadminOpts = []
    commandOpts = []
    command = ""
    flag = False
    prev = ""
    for arg in sys.argv[1:]:
        if flag:
            commandOpts.append(arg)
        else:
            if arg[0] == "-" or prev in ['-s', '--server']:
                cadminOpts.append(arg)
            else:
                command = arg
                flag = True
                
            prev = arg

    return cadminOpts, command, commandOpts


def commandSummary():

    s = ""
    for key in admin.modules.keys():
        s = "%s\n   %s - %s" % (s, key, 
                admin.modules[key].shortHelp)

    return s

    
def main():

    log.info("CADMIN - Current Administration Text Interface")
    log.info("Licensed under the GNU GPL version 2.0 or greater.")

    prefs = Preferences()

    cadminOpts, command, commandOpts = getArguments()
    usage = "usage: %prog [options] COMMAND [options] [arguments]\n"
    usage = usage + commandSummary()

    parser = optparse.OptionParser(usage)
    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      dest="verbose", help="Be more verbose.")
    parser.add_option("-q", "--quiet", action="store_true", default=False,
                      dest="quiet", help="Supress output")
    parser.add_option("-s", "--server", action="store", default="",
                      dest="server", help="URL for Current server")
    opts, args = parser.parse_args(cadminOpts)

    if command == "":
        parser.print_help()
        sys.exit()

    if opts.verbose:
        log.setLevel(logging.DEBUG)

    if opts.quiet:
        log.setLevel(logging.WARNING)

    if command not in admin.modules.keys():
        parser.print_help()
        sys.exit()
    
    print
    session = prefs.getLogin()
    server = getServer(opts.server)
    module = admin.modules[command]

    try:
        log.debug("Running module: %s, %s" % (command, module))
        ret = module.run(server, session, commandOpts)
        log.debug("Module returned: %s" % ret)
    except CurrentRPCError, e:
        print "An error occured.  The error message is:"
        print str(e)

    if command == "login":
        prefs.setLogin(ret)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Interupted by user command"

## END OF LINE ##    
