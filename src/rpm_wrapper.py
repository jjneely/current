""" Wrapper module around rpmlib.

Because the rpm module has so many quirks that may affect current, we 
encapsulate all the direct rpm interactions in this module, so that the 
backends and other code see a single, sane, consistent interface.

Current has also had several rpm related bugs, so bug fixes here will 
automatically fix all the backends.

Update begun 10-Feb-2003 to create a "factory" function / class which makes
the differences between the 4.0.4 and 4.1 API's invisible to the rest of
Current.  Will need relatively extensive testing.

"""

import os
import os.path
import rpm
import stat
from logger import *
import types

class rpmWrapper:
    def __init__(self):
        # Determine which API version we're dealing with
        if rpm.__dict__.has_key('ts'):
            self.API = '4.1'
        else:
            self.API = '4.0.4'
        self.info = None

    def readPackage(self, filename):
        # This routine gets the header object from the given RPM file
        # and gets ready to serve requests.
        # First, ensure the package exists and is readable.
        if not os.access(filename, os.R_OK):
            log("ERROR: Could not read given filename: %s" % (filename,) )
            self.info = None
            return None
        
        # We may need to split off behavior at an earlier or later point...
        # this is a first scratch.  Probably gonna be a lot of duplication.
        # Just deal with it, I'll clean it up later.
        if self.API == '4.0.4':
            self.info = self._read404(filename)
        if self.API == '4.1':
            self.info = self._read41(filename)
        # Allows for easy expansion for future API changes....

    def getRpmInfo(self, pathname = None):
        # This is what proivides the information to the caller - it's the
        # same as the old function of this name, but encapsulated.
        # Be warned, we may need to do additional error checking in the caller
        # for a possible None return value.
        if self.info == None and pathname == None:
            return None
        if pathname != None:
            self.readPackage(pathname)
        return self.info

    def _read404(self, filename):
        # We know the file is readable 'cause it was tested earlier.
        # Read the header from the file.
        try:
            fd = os.open(filename, os.O_RDONLY)
            (header, isSource) = rpm.headerFromPackage(fd)
            os.close(fd)
        except:
            logException()
            log ("ERROR: Error reading RPM package %s" % (filename,) )
            return None
        # Now we build the self.info stuff
        info = {}
        info['pathname'] = filename
        info['issrc'] = isSource
        info['size'] = str(os.stat(filename)[stat.ST_SIZE])
        info['name'] = hdr[rpm.RPMTAG_NAME]
        info['version'] = hdr[rpm.RPMTAG_VERSION]
        info['release'] = hdr[rpm.RPMTAG_RELEASE]
        info['arch'] = hdr[rpm.RPMTAG_ARCH]
        epoch = hdr[rpm.RPMTAG_EPOCH]
        if epoch == None:
            info['epoch'] = ''
        else:
            info['epoch'] = str(epoch)
        info['dep_files'] = hdr[rpm.RPMTAG_FILENAMES]
        info['dep_provides'] = []
        pnames = hdr[rpm.RPMTAG_PROVIDENAME]
        pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS]
        pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
        if pnames != None:
            if type(pflags) != types.ListType:
                pflags = [pflags]
            if type(pvers) != types.ListType:
                pvers = [pvers]
            for i in range(len(pnames)):
                info['dep_provides'].append([pnames[i], str(pflags[i]), pvers[i]])
        info['obsoletes'] = []
        onames = hdr[rpm.RPMTAG_OBSOLETENAME]
        overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
        oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
        if onames != None:
            if type(oflags) != types.ListType:
                oflags = [oflags]
            if type(overs) != types.ListType:
                overs = [overs]
            for i in range(len(onames)):
                info['obsoletes'].append([onames[i], str(oflags[i]), overs[i]])
        info['srpm'] = hdr[rpm.RPMTAG_SOURCERPM]
        # This little item here may cause issues...  I think the only thing we
        # do is call it's unload() method, but we'll have to check.
        info['hdr'] = hdr
        return info


    def _read41(self, filename):
        # First, suck in the header.
        ts = rpm.TransactionSet("/", rpm._RPMVSF_NOSIGNATURES)
        fd = os.open(filename, os.O_RDONLY)
        hdr = ts.hdrFromFdno(fd)
        os.close(fd)
        info = {}
        info['pathname'] = filename
        info['issrc'] = hdr[rpm.RPMTAG_SOURCEPACKAGE]
        info['size'] = str(os.stat(filename)[stat.ST_SIZE])
        info['name'] = hdr[rpm.RPMTAG_NAME]
        info['version'] = hdr[rpm.RPMTAG_VERSION]
        info['release'] = hdr[rpm.RPMTAG_RELEASE]
        info['arch'] = hdr[rpm.RPMTAG_ARCH]
        epoch = hdr[rpm.RPMTAG_EPOCH]
        if epoch == None:
            info['epoch'] = ''
        else:
            info['epoch'] = str(epoch)
        info['dep_files'] = hdr[rpm.RPMTAG_FILENAMES]
        info['dep_provides'] = []
        pnames = hdr[rpm.RPMTAG_PROVIDENAME]
        pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS]
        pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
        if pnames != None:
            if type(pflags) != types.ListType:
                pflags = [pflags]
            if type(pvers) != types.ListType:
                pvers = [pvers]
            for i in range(len(pnames)):
                info['dep_provides'].append([pnames[i], str(pflags[i]), pvers[i]])
        info['obsoletes'] = []
        onames = hdr[rpm.RPMTAG_OBSOLETENAME]
        overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
        oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
        if onames != None:
            if type(oflags) != types.ListType:
                oflags = [oflags]
            if type(overs) != types.ListType:
                overs = [overs]
            for i in range(len(onames)):
                info['obsoletes'].append([onames[i], str(oflags[i]), overs[i]])
        info['srpm'] = hdr[rpm.RPMTAG_SOURCERPM]
        # This little item here may cause issues...  I think the only thing we
        # do is call it's unload() method, but we'll have to check.
        info['hdr'] = hdr
        return info



# We need to figure out what to do with this routine...
def rpmVerCmp( evr1, evr2 ):
    result = rpm.labelCompare(evr1, evr2)
    if (result < 0 ):
        return -1
    elif ( result == 0 ):
        return 0
    else:
        return 1