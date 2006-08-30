#! /usr/bin/python
#
# program configuration module
#

import pprint
import exception
import os
import os.path
import ConfigParser
import logging

## Program wide config object
## Created by current/cadmin/cinstall main()
config = None

## These are replaced by make, so beware
VERSION="1.7.2"
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
    "template_dir": "/usr/share/current/templates",
}


class Config(object):
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
            if opt == '__name__':
                continue
            else:
                value = parser.get('current', opt)
                tmp[opt] = value

        # Quick fix
        return tmp


    def dump(self, file):
        tmp = "Configuration:\n" + pprint.pformat(self._data) + "\n"
        file.write(tmp)


class Configuration(object):

    type = None

    def __init__(self, cf="", defaults=None):
        self.cfg = ConfigParser.ConfigParser(defaults)
        self.configFiles = [cf, '/etc/current/current.conf']
        files = self.cfg.read(self.configFiles)
        
        if files == None:
            raise Exception("Configuration file not found.")

    def get(self, key, default=None, check=None):
        try:
            ret = self.cfg.get(self.type, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            if default != None:
                ret = default
            else:
                s = "Missing Configuration Item: Secion %s, Option %s"
                raise exception.ConfigurationError(s % (self.type, key))

        if check:
            check(ret)

        return ret

    def record(self, key, value):
        if not self.cfg.has_section(self.type):
            self.cfg.add_section(self.type)

        self.cfg.set(self.type, key, value)

        for file in self.configFiles:
            if os.access(file, os.W_OK):
                fd = open(file, 'w')
                self.cfg.write(fd)
                fd.close()
                logging.getLogger().info("Wrote config file: %s" % file)
                return

        raise exception.ConfigurationError(     \
                "Could not save %s=%s in configuration file" % (key, value))

    def checkFile(self, file, message="Missing file: %s"):
        if not os.access(file, os.R_OK):
            raise exception.ConfigurationError(message % file)
    

class Current(Configuration):

    type = "current"

    def __init__(self):
        global defaults
        Configuration.__init__(self, defaults=defaults)

    def getApacheConfigFile(self):
        return self.get("apache_config_file")

    def getLogFile(self):
        return self.get("log_file")

    def getLogLevel(self):
        return self.get("log_level")


class AbstractPreferences(Configuration):

    filename = ".cadmin"

    def __init__(self):
        fn = os.path.join(os.environ['HOME'], self.filename)
        if not os.path.exists(fn):
            # Create file if needed
            fd = open(fn, 'w')
            fd.close()
            
        self.cfg = ConfigParser.ConfigParser()
        self.configFiles = [fn]
        files = self.cfg.read(self.configFiles)
        
        # !!Always, use defaults in this class!!
    

class Preferences(AbstractPreferences):

    type = "preferences"
    
    def getLogin(self):
        return self.get("session", default="Bad Session")

    def setLogin(self, session):
        self.record("session", session)

