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
VERSION="0.20030731"
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


    def load(self):
        self._data = self.readConfigFile(self._defaults['config_file'])

        # merge the defaults in
        for (key, value) in self._defaults.items():   
            if not self._data.has_key(key):
                self._data[key] = value
            # else do nothing - don't override earlier value

        del self._defaults

        
    def __getitem__(self, item):
	""" We support config[key] type access."""
        return self._data.get(item, "")


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

