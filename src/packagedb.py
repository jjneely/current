#! /usr/bin/python

""" PackageDB represents the backend portion concerned with packages.

The api modules (up2date, errata, etc) make calls into the PackageDB (and
ClientDB, etc) - the api modules have no knowledge of the channels
themselves. Conversely, PackageDB only knows of the public interface to the
Channels.

Please note that the compat_arches_table and related functions are from the
up2dateUtils.py file from RH's up2date client. That files copyright info
follows:

 Client code for Update Agent
 Copyright (c) 1999-2001 Red Hat, Inc.  Distributed under GPL.

 Author: Preston Brown <pbrown@redhat.com>
         Adrian Likins <alikins@redhat.com>

"""

import string
import operator
import os

import misc
import channel
from logger import *
db = None


class PackageDB:
    """ The entire package database.
    
    Represents the entire backend, which is composed mostly of Channels
    and the logic to connect a channel to a client.
    """
    
    def __init__(self):
        self.channels = {}
        self.index = {}


    def addChannel(self, chan_info):
        # Everything we need to know about the channel is kept in a 
        # channel object. Just instantiate and read in the new channel.

        tmp = channel.Channel()
        tmp.open(chan_info, 'r')

        # FIXME: we may also need some of the other channel information 
        #    indexed.
        new_label = tmp.chanInfo['label']
        new_arch = tmp.chanInfo['arch']
        new_rel = tmp.chanInfo['os_release']

        # Add channel object itself
        self.channels[new_label] = tmp

        # Now add that chan to our EasyBake(tm) lookup index
        if self.index.has_key(new_arch):
            if self.index[new_arch].has_key(new_rel):
                raise Exception('Cannot have two chans with same properties')
            else:
                self.index[new_arch][new_rel] = new_label
        else:
            self.index[new_arch] = {}
            self.index[new_arch][new_rel] = new_label
            

    def getCompatibleChannels(self, client_arch, client_release):
        """ Scan our channel collections for ones that will work for this client.

        We return a list of 'chanInfo' dict's. 

        """

        logfunc(locals())

        # determine the clients cannonical arch
        ## FIXME: can return None
        cannon = _getCannonArch(client_arch)

        # FIXME: Right now, we assume only one channel will match.
        # see if we have a match for a [cannon][os_release] pair
        if self.index.has_key(cannon):
            if self.index[cannon].has_key(client_release):
                label = self.index[cannon][client_release]
            else:
                # Have that cannonical arch, but not that release
                return []
        else:
            # We don't server that arch, at any release level
            return []
        
        return [self.channels[label].chanInfo]


    def getPackageList(self, chan_label, chan_version):
        """ Get the list of packages for a particular channel. 

        This method is a little strange, as the output is already xmlrpc
        formatted for us. 

        FIXME: This really needs to do something intelligent with the 
        version.

        """

        logfunc(locals())

        list_filename = self.channels[chan_label].getPackageListCache()
        log('List filename being returned: %s' % list_filename, DEBUG2)
        return list_filename
 

    def OLDgetPackageList(self, chan_label):
        logfunc(locals())

        # FIXME: This could fail.
        pkg_list = self.channels[chan_label].getList()

        # pkg_list is [ 
        # pkg1           [ NVREAS, NVREAS, NVREAS ] 
        # pkg2           [ NVREAS ] 
        # pkg3           [ NVREAS, NVREAS ]
        #  etc        ]

        # We flatten this list out into a single list.

        # Note: earlier up2date clients only wanted a single entry for 
        # each package - the _server_ picked the best package for a client

        # In 2.7 and later clients, the _client_ picks the best fit from
        # all available packages.

        # FIXME: we should cache this as an xmlrpc encoded file somewhere
        # and just return that. The file could be created with the DB,
        # saving a ton of run-time processing.
        client_list = reduce(operator.add, pkg_list)
        map(lambda a, chan_label=chan_label:a.append(chan_label), client_list)

        return client_list

        
    def solveDependancy(self, chan_label, client_arch, unknown):
        logfunc(locals())

        # This call will not fail - it'll return None if nothing found.
        pick_list = self.channels[chan_label].getDependancy(unknown)

        return pick_list


    def getPackageFilename(self, chan_label, package):
        """ Get the filename for a particular rpm. """

        logfunc(locals())

        return self.channels[chan_label].getRpmFilename(package)
            

    def getPackageHeaderFilename(self, chan_label, header_name):

        logfunc(locals())

        return self.channels[chan_label].getPackageHeaderCache(header_name)

        
    def getSrcPackageFilename(self, chan_label, package):
        """ Get the filename for a particular source rpm. 

        This ones nice - we get a string, look it up in a dict, return.

        """
    
        # FIXME: This could fail.
        current_pick = self.channels[chan_label].getSrcRpmFilename(package)

        return current_pick
            

    # Obsolete code. Remove in v1.1
    def _pickBestPackage(self, client_arch, pick_list):
        """ From a list of NVREAS sub-lists, pick the best fit for client """

        # for the packages in pick_list, pick the NVREAS (which is a list as
        # well) that will work best on this particular client. Which might
        # be none of them, as in the case of kernel-smp [i586 & i686] being
        # sent to an i486.

        logfunc(locals())
        
        current_score = 1000      # some artificially high number
        current_pick = None       # default is no match, for safety
        for pick in pick_list:
            pick_score = _scoreArch(client_arch, pick[4])
            log("  pick = %s" % pick, TRIVIA)
            log("  pick_score = %s" % pick_score, TRIVIA)
            if (pick_score != -1 and pick_score < current_score):
                log("  pick score was higher than current score", TRIVIA)
                current_score = pick_score
                current_pick = pick

        log("  current_pick = %s" % current_pick, DEBUG2)
        return current_pick


# Tragically, it looks like we'll need at least the table and _getCannonArch
# even for 2.7 clients - we need to know which channels will work for a 
# given client.

# NOTE: The order of the stuff in compat is in newest->latest order
# assuming backwards compability
_compat_arches_table = {
    # ARCH      : # CANON,      # COMPAT
    "noarch"    : [ "noarch",   "noarch" ],
    "i386"      : [ "i386",     "i386", "noarch" ],
    "i486"      : [ "i386",     "i486", "i386", "noarch" ],
    "i586"      : [ "i386",     "i586", "i486", "i386", "noarch" ],
    "i686"      : [ "i386",     "i686", "i586", "i486", "i386", "noarch" ],
    "athlon"    : [ "i386",     "athlon", "i686", "i586", "i486", "i386", "noarch" ],
    "alpha"     : [ "alpha",    "alpha", "noarch" ],
    "alphaev6"  : [ "alpha",    "alphaev6", "alpha", "noarch" ],
    "sparc"     : [ "sparc",    "sparc", "noarch" ],
    "sparcv9"   : [ "sparc",    "sparcv9", "sparc", "noarch" ],
    "sparc64"   : [ "sparc",    "sparc64", "sparc", "noarch" ],
    "ia64"      : [ "ia64",     "ia64", "noarch" ],
    "src"       : [ "SRPMS",    "src" ],
    }


# translate an arch into its basename platform name
def _getCannonArch(arch):
    logfunc(locals())

    # XXX: this should not be really happening
    if not arch in _compat_arches_table.keys():
        log("ERROR: Can not locate architecture in internal database", 
            MANDATORY)
        log("Looking for %s in %s\n" % (arch, repr(_compat_arches_table)), 
            MANDATORY)
        return None
    return _compat_arches_table[arch][0]


# Get a list of compatible cpus
def _getCompatibleArchs(arch):
    logfunc(locals())
    # XXX: this should not be really happening
    if not arch in _compat_arches_table.keys():
        log("ERROR: Can not locate architecture in internal database", 
            MANDATORY)
        log("Looking for %s in %s\n" % (arch, repr(_compat_arches_table)), 
            MANDATORY)
        return None
    return _compat_arches_table[arch][1:]


def _scoreArch(sys_arch, arch):
    logfunc(locals())

    sys_compat_arches = _getCompatibleArchs(sys_arch)

    if arch not in sys_compat_arches:
        # Not compatible with this arch
        res = -1
    else:
        res = sys_compat_arches.index(arch)

    log("  _scoreArch() returned %s" % res, DEBUG2)
    return res


def _compareArchs(sysArch, oldArch, newArch, prefer_sysArch = 1):

    """ just past in sysArch since theres not really any point in
    recomputing it.

    sysArch is the arch of the actual system
    oldArch is the arch of the currently installed package
    newArch is the arch of the package were considering installing
    
    return value is a score of the newArch relative to the
    (sysArch, oldArch) pair, with oldArch being given priority
    A return of -1 signals incompatibility
    """

    sysCompatArches = _getCompatibleArchs(sysArch)
    oldCompatArches = _getCompatibleArchs(oldArch)

    # We need data to work with
    if None in [sysCompatArches, oldCompatArches]:
        # there are no compatible arches for this system. Uh oh.
        return -1

    # A few sanity checks
    if newArch not in sysCompatArches:
        # the arch isnt supported on this platform
        return -1
    
    # if we prefer affinity to the system architecture, then we always
    # score against the sysArch list.
    if prefer_sysArch:
        return sysCompatArches.index(newArch)

    # If we prefer affinity to the arch of the installed package, do some
    # more checks.
    if oldArch not in sysCompatArches:
        # the version of the installed package is not compatible!!!
        return -1
    # Give preference to matches against the oldCompatArches
    if newArch in oldCompatArches:
        return oldCompatArches.index(newArch)
    # Otherwise, handicap the match into sysCompatArches by the distance of
    # oldArch from sysCompatArches
    return sysCompatArches.index(newArch) + sysCompatArches.index(oldArch)


if __name__ == "__main__": 
    pass    
            
## END OF LINE ##
