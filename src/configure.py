#! /usr/bin/python
#
# program configuration module
#

import string
import pprint
import sys
import exceptions
import getopt
import os
import re
import ConfigParser

## Program wide config object
## Created by current/cadmin/cinstall main()
config = None

## These are replaced by make, so beware
VERSION="1.5.4"
MODULES_DIR="/usr/share/current"
CONFIG_DIR="/etc/current"
LOG_DIR="/var/log/httpd"
PID_DIR="/var/run"


## Program wide defaults
# The default defaults, as it were
defaults = {
    "version": VERSION,
    "config_file": CONFIG_DIR + "/current.conf",
    "apache_config_file": "/etc/httpd/conf.d/current.conf",
    "log_file":    LOG_DIR + "/current.log",
    "log_level":   0,
}


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
    """ The configuration object for the current server. 
    
    The config objects precedence from most important to least is 
    command line -> enviroment -> config file -> defaults. 

    However to find things, we have to read them in the order 
    defaults -> cmdline -> enviroment -> file. 

    So, we store the defaults seperately, and read each config source in
    turn. If a later source (say the file) contains information (log level)
    that we've already seen (say the command line), we ignore the newest 
    information. In other words, first hit wins.

    """

    def __init__(self, defaults={}):
        self._data = {}
        self._defaults = defaults


    def load(self, apache=1):
        # Only look at cmd line args if we're not inside apache / mod_python
        if not apache:  
            self._data = self.readCommandLine(sys.argv)

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

        
#     def __getattr__(self, item):
# 	""" We support config.key type access. """
#         return self._data.get(item, "")


    def __getitem__(self, item):
	""" We support config[key] type access."""
        return self._data.get(item, "")

    def __str__(self):
        return str(self._data)

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
        usage = """Usage: %s [options]
  -c, --config    config file to use 
  -d, --dump      dump final configuration and exit
  -h, --help      print this help and exit
  -v, --verbose   increase level of logging (can use more than once)
  -V, --version   print version and exit""" % os.path.basename(sys.argv[0])
        
        usage_requested = 0
        tmp = {}

        try:
            opts, args = getopt.getopt(argv[1:], "c:dhvV", 
                         ("config=", "dump", "help", "verbose", "version"))
        except getopt.error, msg:
            sys.stdout = sys.stderr
            print msg
            print usage
            sys.exit(2)
   
        # These are clearly  a kludge
        tmp["args"] = args
        
        for o, a in opts:
            if o in ("-c", "--config"):
                tmp["config_file"] = a
            if o in ("-d", "--dump"):
                tmp["dump"] = 1
            if o in ("-h", "--help"):
                usage_requested = 1
            if o in ("-v", "--verbose"): 
                tmp["log_level"] = tmp.get('log_level', 0) + 1
            if o in ("-V", "--version"):
                print "current v%s (C) 2001,2002 Hunter Matthews" % \
                    self._defaults["version"]
                print "Released under the GPL"
                sys.exit(0)
        
        if usage_requested:
            print usage
            sys.exit(0)

        return tmp


    def readConfigFile(self, filename):
        tmp = {}

        # BUGFIX: If there is no config file, return now. This can happen
        # either during development, or before a user has a proper config
        # file.
        if not os.path.isfile(filename):
            return tmp

        parser = ConfigParser.ConfigParser()
        parser.read(filename)
        
        for opt in parser.options('current'):
            if opt == 'valid_channels':
                tmp[opt] = string.split(parser.get('current', opt))
            elif opt == '__name__':
                continue
            else:
                value = parser.get('current', opt)
                tmp[opt] = value

        # Quick fix
        return tmp

        tmp['channels'] = {}

        # A little hackery 
        # Our output is a dict with the keys being the channel labels.
        for label in tmp['valid_channels']:
            try:
                tmp['channels'][label] = {'label': label}
                options = parser.options(label)
            except ConfigParser.NoSectionError:
                raise MissingError("Section %s not found - perhaps this is an older config file?" % label)

            for opt in options:
                if opt == '__name__':
                    continue
                elif opt == 'rpm_dirs' or opt == 'src_dirs':
                    tmp['channels'][label][opt] = \
                        string.split(parser.get(label, opt))
                else:
                    tmp['channels'][label][opt] = parser.get(label, opt)

            # Add the "calculated" db_dir and web_dir values to each
            # channel dict.
            # We need two: web_dir parts are available to apache/mod_python
            # and I don't think the db_dir parts should be.
            try:
                tmp['channels'][label]['db_dir'] = \
                    os.path.join(tmp['current_dir'], 'db', label)
                tmp['channels'][label]['web_dir'] = \
                    os.path.join(tmp['current_dir'], 'www', label)
            except KeyError:
                raise MissingError("db_dir or web_dir not found - perhaps this is an older config file?")
            
            # Make sure the user included the srpm_check value - it was
            # optional, now its required.
            if not tmp['channels'][label].has_key('srpm_check'):
                raise MissingError("You must include the srpm_check value\n "+\
                    "'srpm_check = 0' is the old default")

        return tmp


    def dump(self, file):
        tmp = "Configuration:\n" + pprint.pformat(self._data) + "\n"
        file.write(tmp)

## END OF LINE ##

