# This package/module contains the modules for cadmin

import glob
import os.path
import sys

sys.path.append('/usr/share/rhn')
from up2date_client import rpcServer

class CadminConfig(object):

    shortHelp = "No help description avaliable."

    def run(self, server, argv):
        pass

    def name(self):
        return "AbstractConfigClass"


import test
import scan
import create_channel
import add_dir

modules = {}
modules['test'] = test
modules['scan'] = scan
modules['create_channel'] = create_channel
modules['add_dir'] = add_dir

