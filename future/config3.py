#! /usr/bin/python
##
## program configuration module
##

import ConfigParser
import string
import pprint
import sys
import exceptions
import getopt
import os

# I include this here because I hope to make this module project portable. 
# This is PRCS magic
# $Format: "__REVISION = '$Revision: 1.3 $'"$
__REVISION = '1.2'

class Types:
    """ Basically a list of possible values (like an enum in C) """
    # Clap has float as a type, but I don't see where that would be useful
    # Someone else could add it...

    Null = 0               # Not a real type - just a flag for 'invalid'
    Flag = 1
    Int = 2
    String = 3
    Counter = 4
    IntList = 5
    StringList = 6 


# Configuration Exceptions
class Error(exceptions.Exception):
    pass

class FormatError(Error):
    """ Passed wrong _type_ of for a command line argument, or the config
    file is bogus. """
    pass

class MissingError(Error):    
    """ A required configuration value wasn't found after all processing."""
    pass


class Config:

    def __init__(self, table)
        self._table = table


    def load(self):
        self._data = self.readCommandLine(sys.argv)

        # For later config sources, we must NOT replace earlier data 
        # elements - the enviroment overrides the config file, and the 
        # command line overrides everything. 
        tmp = self.readEnviroment(os.environ)
        for (key, value) in tmp.items():
            if not self._data.has_key(key):
                self._data[key] = value
            # else do nothing - don't override earlier value

        # if we don't do this test, we won't ever pick up the cmdline   
        # value for the config file.
        if self._data.has_key('config_file'):
            file = self._data['config_file']
        else:
            file = self._defaults['config_file']
            
        tmp = self.readConfigFile(file)
        for (key, value) in tmp.items():
            if not self._data.has_key(key):
                self._data[key] = value
            # else do nothing - don't override earlier value

        # last step is to merge the defaults in
        for (key, value) in self._defaults.items():   
            if not self._data.has_key(key):
                self._data[key] = value
            # else do nothing - don't override earlier value

        del self._defaults

        
    def getItem(self, item):
        # deliberately fail - we shouldn't get asked if we don't know - 
        # the defaults should cover that sort of thing.
        return self._data[item]


    def verify(self):
        pass

    
    def readEnviroment(self, environ):
        # FIXME: we accept nothing
        return {}

    
    def readCommandLine(self, argv):
        """ Read the command line.
        
        Command line overrides any other source of config sources.
        
        """

        ## FIXME: this should be outside the base class somewhere    
        usage = """Usage: current [options]
  -c, --config    config file to use 
  -d, --dump      dump final configuration and exit
  -h, --help      print this help and exit
  -l, --logfile   log file to use
  -v, --verbose   increase level of logging (can use more than once)
  -V, --version   print version and exit"""
        
        usage_requested = 0
        tmp = {}

        try:
            opts, args = getopt.getopt(argv[1:], "c:dhl:vV", 
                         ("config=", "dump", "help", "logfile=", "verbose", 
                          "version"))

        except getopt.error, msg:
            sys.stdout = sys.stderr
            print msg
            print usage
            sys.exit(2)
   
        # These are clearly  a kludge
        tmp["args"] = args
        
        for o, a in opts:
            if o == "-c" or o == "--config":
                tmp["config_file"] = a
            if o == "-d" or o == "--dump":
                tmp["dump"] = 1
            if o == "-h" or o == "--help":
                usage_requested = 1
            if o == "-l" or o == "--logfile":
                tmp["log_file"] = a
            if o == "-v" or o == "--verbose": 
                if not tmp.has_key('log_level'):
                    tmp["log_level"] = 1
                else:
                    tmp["log_level"] = tmp["log_level"] + 1
            if o == "-V" or o == "--version":
                print "current v%s (C) 2001 Hunter Matthews" % \
                    self._defaults["version"]
                print "Released under the GPL"
                sys.exit(0)
        
        if usage_requested:
            print usage
            sys.exit(0)

        return tmp


    def readConfigFile(self, filename):
        tmp = {}
        parser = ConfigParser.ConfigParser()

        # Gross hack to allow periods in section names...
        parser._ConfigParser__SECTCRE = re.compile(
            r'\['                                 # [
            r'(?P<header>[-.\w]+)'                 # `-', `_' or any alphanum
            r'\]'                                 # ]
            )
        parser.read(filename)
        
        for opt in parser.options('global'): # global is what samba uses...
            if opt == 'repository_list':
                tmp[opt] = string.split(parser.get('global', opt))
            elif opt == '__name__':
                continue
            else:
                tmp[opt] = parser.get('global', opt)

        tmp['repositories'] = {}
        for repository in tmp['repository_list']:
            tmp['repositories'][repository] = {}
            for opt in parser.options(repository):
                if opt == '__name__':
                    continue
                elif opt == 'rpm_dirs' or opt == 'src_dirs':
                    tmp['repositories'][repository][opt] = \
                        string.split(parser.get(repository, opt))
                else:
                    tmp['repositories'][repository][opt] = parser.get(repository, opt)

        return tmp


    def dump(self, file):
        tmp = "Configuration:\n" + pprint.pformat(self._data) + "\n"
        file.write(tmp)


def main():
args = [
         "help", # special flag meaning do -h/--help from 1-3rd arg
         "usage", # special flag meaning do --usage from 1st, 5th args
         [ 'c', 'config', 'Config file to use', Type.String, 'FILE', 'cfe', 'current.conf' ],
         [ 'd', 'dump', 'Dump final configuration and exit', Type.Flag, None, 'c', None ],
         [ 'l', 'logfile', 'Log file to use', Type.String, 'FILE' 'cf', 'current.log'],
         [ 'v', 'verbose', 'Increase level of logging ++', Type.Counter, None, 'cf', '10' ],
         [ 'V', 'version', 'Print version and exit', Type.Flag, None, 'c', None ]
       ]        

    cfg = Config(args)


if __name__ == "__main__": 
    main()

## END OF LINE ##

