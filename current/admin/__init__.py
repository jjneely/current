# This package/module contains the modules for cadmin

import glob
import os
import os.path
import sys
import logging
import optparse

modules = None

# Abstract Object for cadmin modules
class CadminConfig(object):

    shortHelp = "No help description avaliable."

    def run(self, server, argv):
        pass

    def name(self):
        return "AbstractConfigClass"

    def defaultParser(self, usage):
        parser = optparse.OptionParser(usage)
        parser.add_option("-l", "--label", action="append", 
                          type="string", dest="channels")
        parser.add_option("-u", "--uuid", action="append", 
                          type="string", dest="uuid")
        return parser


def getModules():
    log = logging.getLogger("cadmin")
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

