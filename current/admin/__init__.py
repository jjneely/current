# This package/module contains the modules for cadmin

import glob
import os
import os.path
import sys
import logging
import optparse

from current import xmlrpc
from current import exception

modules = None
log = logging.getLogger("cadmin")

# Abstract Object for cadmin modules
class CadminConfig(object):

    shortHelp = "No help description avaliable."

    def run(self, server, argv):
        pass

    def name(self):
        return "AbstractConfigClass"

    def call(self, method, *args):
        try:
            return xmlrpc.doCall(method, *args)
        except xmlrpc.Fault, e:
            log.error("A Server Fault occured: %s" % str(e))
            sys.exit(2)
        except exception.CurrentRPCError, e:
            log.error("An error occured communicating with the server: %s" \
                      % str(e))
            sys.exit(3)
            
    def defaultParser(self, usage):
        parser = optparse.OptionParser(usage)
        parser.add_option("-l", "--label", action="append", default=[],
                          type="string", dest="channels")
        parser.add_option("-u", "--uuid", action="append", default=[],
                          type="string", dest="uuid")
        return parser


def getModules():
    list = []
    modules = {}
    path = os.path.dirname(__file__)

    log.debug("Loading admin modules from path: %s" % path)

    files = os.listdir(path)
    for file in files:
        if file.startswith('_'):
            continue
        if file.startswith('.'):
            continue
        if not file.endswith('.py'):
            continue
        list.append(file[:-3])

    for m in list:
        try:
            mod = __import__(m, globals(), locals(), ['current.admin'])
        except ImportError, e:
            log.error("Failed to import module: %s" % m)
            continue

        for n, obj in mod.__dict__.items():
            if not type(obj) == type(object):
                continue
            if not issubclass(obj, CadminConfig):
                continue
            if obj is CadminConfig:
                continue
            
            modules[m] = obj()

    return modules

if modules == None:
    modules = getModules()

