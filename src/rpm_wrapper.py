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

# Testing indicates there is a minimal speed increase with the newer
# __getattr__ model, but this is on the order of a few seconds (<5) in a 13
# to 15 minute run for a single tree.  Nevertheless, we'll start using the
# new model, hoping for future speed increases from it as we refine it.

class rpmWrapper:
    def __init__(self):
        # Determine which API version we're dealing with
        if rpm.__dict__.has_key('ts'):
            self.API = '4.1'
        else:
            self.API = '4.0.4'
        self.info = None

    def getRpmInfo(self, pathname = None):
        # This is what proivides the information to the caller - it's the
        # same as the old function of this name, but encapsulated.
        # Be warned, we may need to do additional error checking in the caller
        # for a possible None return value.
        if self.info == None and pathname == None:
            self.error = 1
            return
        if pathname != None:
            self.error = 0
            self.readPackage(pathname)

    def readPackage(self, filename):
        # This routine gets the header object from the given RPM file
        # and gets ready to serve requests.
        # First, ensure the package exists and is readable.
        if not os.access(filename, os.R_OK):
            log("ERROR: Could not read given filename: %s" % (filename,) )
            return -1
        
        # We may need to split off behavior at an earlier or later point...
        # this is a first scratch.  Probably gonna be a lot of duplication.
        # Just deal with it, I'll clean it up later.
        if self.API == '4.0.4':
            self._read404(filename)
        if self.API == '4.1':
            self._read41(filename)
        # Allows for easy expansion for future API changes....
        return 1

    def _read404(self, filename):
        # We know the file is readable 'cause it was tested earlier.
        # Read the header from the file.
        self.error = 0
        try:
            fd = os.open(filename, os.O_RDONLY)
            (self.hdr, self.isSrc) = rpm.headerFromPackage(fd)
            self.pathname = filename
            os.close(fd)
        except:
            logException()
            log ("ERROR: Error reading RPM package %s" % (filename,) )
            self.error = 1

    def _read41(self, filename):
        # First, suck in the header.
        self.error = 0
        try:
            ts = rpm.TransactionSet("/", rpm._RPMVSF_NOSIGNATURES)
            fd = os.open(filename, os.O_RDONLY)
            self.hdr = ts.hdrFromFdno(fd)
            self.pathname = filename
            os.close(fd)
        except:
            logException()
            log ("Reading file - not an RPM?")
            self.error = 1
            return
        if ( self.hdr == None ):
            self.error = 1
            return None

    def __getitem__(self, key):
        if self.error == 1:
            return None
        if key == 'error':
            return self.error
        elif key == 'pathname':
            return self.pathname
        elif key == 'issrc' and self.API == '4.0.4':
            return self.isSrc
        elif key == 'issrc' and self.API == '4.1':
            return self.hdr[rpm.RPMTAG_SOURCEPACKAGE]
        elif key == 'size':
            return str(os.stat(self.pathname)[stat.ST_SIZE])
        elif key == 'name':
            return self.hdr[rpm.RPMTAG_NAME]
        elif key == 'version':
            return self.hdr[rpm.RPMTAG_VERSION]
        elif key == 'release':
            return self.hdr[rpm.RPMTAG_RELEASE]
        elif key == 'arch':
            return self.hdr[rpm.RPMTAG_ARCH]
        elif key == 'epoch':
            if self.hdr[rpm.RPMTAG_EPOCH] == None:
                return ''
            else:
                return self.hdr[rpm.RPMTAG_EPOCH]
        elif key == 'dep_files':
            return self.hdr[rpm.RPMTAG_FILENAMES]
        elif key == 'srpm':
            return self.hdr[rpm.RPMTAG_SOURCERPM]
        elif key == 'dep_provides':
            ret = []
            pnames = self.hdr[rpm.RPMTAG_PROVIDENAME]
            pflags = self.hdr[rpm.RPMTAG_PROVIDEFLAGS]
            pvers = self.hdr[rpm.RPMTAG_PROVIDEVERSION]
            if pnames != None:
                if type(pflags) != types.ListType:
                    pflags = [pflags]
                if type(pvers) != types.ListType:
                    pvers = [pvers]
                for i in range(len(pnames)):
                    ret.append([pnames[i], str(pflags[i]), pvers[i]])
            return ret
        elif key == 'dep_obsoletes':
            ret = []
            onames = self.hdr[rpm.RPMTAG_OBSOLETENAME]
            oflags = self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]
            overs = self.hdr[rpm.RPMTAG_OBSOLETEVERSION]
            if onames != None:
                if type(oflags) != types.ListType:
                    oflags = [oflags]
                if type(overs) != types.ListType:
                    overs = [overs]
                for i in range(len(onames)):
                    ret.append([onames[i], str(oflags[i]), overs[i]])
            return ret
        elif key == 'hdr':
            return self.hdr


class rpmOldWrapper:
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
        info['dep_obsoletes'] = []
        onames = hdr[rpm.RPMTAG_OBSOLETENAME]
        overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
        oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
        if onames != None:
            if type(oflags) != types.ListType:
                oflags = [oflags]
            if type(overs) != types.ListType:
                overs = [overs]
            for i in range(len(onames)):
                info['dep_obsoletes'].append([onames[i], str(oflags[i]), overs[i]])
        info['srpm'] = hdr[rpm.RPMTAG_SOURCERPM]
        # This little item here may cause issues...  I think the only thing we
        # do is call it's unload() method, but we'll have to check.
        info['hdr'] = hdr
        return info


    def _read41(self, filename):
        # First, suck in the header.
        try:
            ts = rpm.TransactionSet("/", rpm._RPMVSF_NOSIGNATURES)
            fd = os.open(filename, os.O_RDONLY)
            hdr = ts.hdrFromFdno(fd)
            os.close(fd)
        except:
            logException()
            log ("Reading file - not an RPM?")
            return None
        if ( hdr == None ):
            return None
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
        info['dep_obsoletes'] = []
        onames = hdr[rpm.RPMTAG_OBSOLETENAME]
        overs = hdr[rpm.RPMTAG_OBSOLETEVERSION]
        oflags = hdr[rpm.RPMTAG_OBSOLETEFLAGS]
        if onames != None:
            if type(oflags) != types.ListType:
                oflags = [oflags]
            if type(overs) != types.ListType:
                overs = [overs]
            for i in range(len(onames)):
                info['dep_obsoletes'].append([onames[i], str(oflags[i]), overs[i]])
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