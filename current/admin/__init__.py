# This package/module contains the modules for cadmin

import glob
import os.path
import sys

# Abstract Object for cadmin modules
class CadminConfig(object):

    shortHelp = "No help description avaliable."

    def run(self, server, argv):
        pass

    def name(self):
        return "AbstractConfigClass"


from current.admin import test
from current.admin import scan
from current.admin import create_channel
from current.admin import add_dir

modules = {}
modules['test'] = test
modules['scan'] = scan
modules['create_channel'] = create_channel
modules['add_dir'] = add_dir

