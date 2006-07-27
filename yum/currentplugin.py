#!/usr/bin/python
#
# currentpluging.py - Yum plugin to interoperate with Current 
#
# Copyright 2006 Jack Neely <jjneely@gmail.com>
#
# SDG
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import xmlrpclib
import socket
import httplib
import urllib2
import ConfigParser
import os
import os.path

from tempfile import TemporaryFile
from xmlrpclib import Fault

from yum.config import readRepoConfig, _getsysver
from yum.plugins import TYPE_CORE, PluginYumExit
from rpmUtils import arch 

requires_api_version = '2.4'
plugin_type = (TYPE_CORE,)

# readRepoConfig(ConfigParser, section, c.getConf()

class CurrentRPCError(Exception):
    # Safely exit if we blow up
    pass

def doCall(method, *args, **kwargs):
    """Wrap and Error check XMLRPC calls.
       This was taken from up2date's rpcServer.py and reduces our dependancy
       on up2date which wont always be present."""
    
    ret = None

    attempt_count = 1
    attempts = 5 # XXX: Configurable

    while 1:
        failure = 0
        ret = None        
        try:
            ret = apply(method, args, kwargs)
        except KeyboardInterrupt:
            raise CurrentRPCError(_(
                "Connection aborted by the user"))
        # if we get a socket error, keep tryingx2
        except (socket.error, socket.sslerror), e:
            log("A socket error occurred: %s, attempt #%s" % (
                e, attempt_count), VERBOSE)
            if attempt_count >= attempts:
                if len(e.args) > 1:
                    raise CurrentRPCError(e.args[1])
                else:
                    raise CurrentRPCError(e.args[0])
            else:
                failure = 1
        except httplib.IncompleteRead:
            #print "httplib.IncompleteRead" 
            raise CurrentRPCError("httplib.IncompleteRead")

        except urllib2.HTTPError, e:
            msg = "\nAn HTTP error occurred:\n"
            msg = msg + "URL: %s\n" % e.filename
            msg = msg + "Status Code: %s\n" % e.code
            msg = msg + "Error Message: %s\n" % e.msg
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

        except xmlrpclib.ProtocolError, e:
            msg = "An XMLRPC protocol error occured: %s" % str(e)
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

        except xmlrpclib.ResponseError, e:
            msg = "Server send a broken responce: %s" % str(e)
            log(msg, VERBOSE)
            raise CurrentRPCError(msg)

        if ret != None:
            break
        else:
            failure = 1

        if failure:
            # rest for five seconds before trying again
            time.sleep(5)
            attempt_count = attempt_count + 1
        
        if attempt_count > attempts:
            print "busted2"
            print method
            raise CurrentRPCError(
                    "The data returned from the server was incomplete")

    return ret
    
def getSysID(path):
    dir, file = os.path.split(path)
    if not os.path.exists(dir):
        os.makedirs(dir, 0755)
    
    if not os.path.exists(os.path.join(dir, file)):
        return None

    fd = open(os.path.join(dir, file))
    blob = fd.read()
    fd.close()
    return blob

def register(c, server, path, secret):
    # The directory part of path should already exist as we call 
    # getSysID() first.
    # XXX: secret/activation key support

    configDir = os.path.dirname(path)
    uuidfile = os.path.join(configDir, "uuid")
    basearch = arch.getBaseArch()
    ver = _getsysver(c.getConf().installroot, 
                     c.getConf().distroverpkg)

    if os.path.exists(uuidfile):
        uuid = open(uuidfile).read().strip()
    else:
        uuid = os.popen("/usr/bin/uuidgen -t").read().strip()
        fd = open(uuidfile, 'w')
        fd.write(uuid)
        fd.close()
        os.chmod(uuidfile, 0600)

    # Build up the system_dict
    system = {
        'architecture': basearch,
        'os_release': ver,
        'profile_name': socket.getfqdn(),
        'release_name': 'Current is Cool',
        'rhnuuid': uuid,
        'username': 'foobar',
        'password': 'foobarbaz',
        'token': 'secret',
    }

    ret = doCall(server.registration.new_system, system)

    fd = open(path, 'w')
    fd.write(ret)
    fd.close()
    os.chmod(path, 0600)

    return ret

def runPlugin(c):
    url = c.confString('main', 'url', None)
    systemidpath = c.confString('main', 'systemid', 
                                "/etc/sysconfig/current/systemid")

    if url == None:
        disableCurrent("URL for Current server not found")
        return

    server = xmlrpclib.Server(url)
    sysid = getSysID(systemidpath)
    if sysid == None:
        # Register the system
        sysid = register(c, server, systemidpath, None)

    fd = TemporaryFile()
    fd.write(doCall(server.yum.getYumConfig, sysid))
    fd.seek(0)

    cfg = ConfigParser.ConfigParser()
    cfg.readfp(fd)
    fd.close()

    for section in cfg.sections():
        if section == "main":
            continue
        repo = readRepoConfig(cfg, section, c.getConf())
        c.getRepos().add(repo)

def init_hook(c):
    c.info(3, "Loading Current Support.")

    try:
        return runPlugin(c)
    except (CurrentRPCError, xmlrpclib.Fault), e:
        c.error(1, "An error occured interfacing with Current.")
        c.error(1, str(e))

        print "Current Error: %s" % str(e)

