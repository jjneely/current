""" Wrapper module around rpmlib.

Because the rpm module has so many quirks that may affect current, we 
encapsulate all the direct rpm interactions in this module, so that the 
backends and other code see a single, sane, consistent interface.

Current has also had several rpm related bugs, so bug fixes here will 
automatically fix all the backends.

FIXME: Right now this is hopelessly python 2.2 code - should we back port?
"""

import os
import stat
import types 
import rpm

# namespace silliness
# python 1.5 = rd = {}; for k,v in d.items(): rd[v] = k
# tags = dict(zip(rpm.tagnames.values(), rpm.tagnames.keys()))
tags = {}
for key in dir(rpm):
    if key.startswith('RPMTAG_'): 
        tags[key[7:]] = eval('rpm.' + key)

# Now we add in current specific tags.
tags['CT_FILESIZE'] = 10000
tags['CT_PATHNAME'] = 10001

# Make this part of our modules namespace
locals().update(tags)

# Make sure clients get as clean an import as we can make it
__all__ = tags.keys()
__all__.append('Header')


class Header:
    def __init__(self, pathname):
        """ Note that a client is free to reach inside and grab any of 
            the pathname, file_size, hdr or is_source attributes. """

        self.pathname = pathname
        self.file_size = str(os.stat(pathname)[stat.ST_SIZE])

        (self.hdr, self.is_source) = self._getHeaderFromFilename(pathname)


    def __getitem__(self, key):
        assert key in tags.values()

        if key == tags['SOURCEPACKAGE']:
            # This is insane for 4.1, but required for 4.0 and earlier    
            return not not self.is_source

        elif key == tags['CT_FILESIZE']:
            # fake our own header entries
            return self.file_size

        elif key == tags['CT_PATHNAME']:
            return self.pathname
        
        elif key == tags['EPOCH']:
            # Library return None or an int - we always want string.
            if self.hdr[rpm.RPMTAG_EPOCH] == None:
                return ''
            else:
                return str(self.hdr[rpm.RPMTAG_EPOCH])

        # Rpmlib screws up PROVIDEVERSION and PROVIDEFLAGS when there is 
        # only one. It gets NAME correct (list of length 1), but is broken
        # for these values.
        elif key == tags['PROVIDEVERSION']:
            if type(self.hdr[rpm.RPMTAG_PROVIDEVERSION]) != types.ListType:
                return [self.hdr[rpm.RPMTAG_PROVIDEVERSION]]
            else:
                return self.hdr[rpm.RPMTAG_PROVIDEVERSION]
        elif key == tags['PROVIDEFLAGS']:
            if type(self.hdr[rpm.RPMTAG_PROVIDEFLAGS]) != types.ListType:
                return [self.hdr[rpm.RPMTAG_PROVIDEFLAGS]]
            else: 
                return self.hdr[rpm.RPMTAG_PROVIDEFLAGS]

        # Obsoletes suffers the same trouble as above for PROVIDES
        elif key == tags['OBSOLETEVERSION']:
            if type(self.hdr[rpm.RPMTAG_OBSOLETEVERSION]) != types.ListType:
                return [self.hdr[rpm.RPMTAG_OBSOLETEVERSION]]
            else:
                return self.hdr[rpm.RPMTAG_OBSOLETEVERSION]
        elif key == tags['OBSOLETEFLAGS']:
            if type(self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]) != types.ListType:
                return [self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]]
            else:
                return self.hdr[rpm.RPMTAG_OBSOLETEFLAGS]

        # Its normal, and we just return it.
        else:
            return self.hdr[key]


    def _getHeaderFromFilename(self, pathname):
        """ Open a pathname as an rpm, and retrive the header from it. """
                                                                                    
        # multiplexor function to handle the different rpm API's.
        if hasattr(rpm, 'ts'):
            return self._getHeaderFromFilename41(pathname)
        else:
            return self._getHeaderFromFilename40(pathname)
                                                                                    
                                                                                    
    def _getHeaderFromFilename40(self, pathname):
        """ Open a pathname as an rpm, using the rpm 3.0 -> 4.0 rpmlib API """

        try:
            fd = os.open(pathname, os.O_RDONLY)
            (header, isSource) = rpm.headerFromPackage(fd)
            os.close(fd)
        except:
#            logException()
            print "Warning: Could not open package %s" % pathname
            return (None, None)
            
        if header == None:
            print "Warning: Could not read package %s" % pathname
            return (None, None)
        else:
            return (header, isSource)
    
    
    def _getHeaderFromFilename41(self, pathname):
        """ Open a pathname as an rpm, using the rpm 4.1+ rpmlib API """

        try:
            ts = rpm.TransactionSet("/", rpm._RPMVSF_NOSIGNATURES)
            fd = os.open(pathname, os.O_RDONLY)
            header = ts.hdrFromFdno(fd)
            isSource = header[rpm.RPMTAG_SOURCEPACKAGE]
            os.close(fd)
        except:
#            logException()
            print "Warning: Could not open package %s" % pathname
            return (None, None)
                                                                                    
        if header == None:
            print "Warning: Could not read package %s" % pathname
            return (None, None)
        else:                                                                                
            return (header, isSource)


# We need to figure out what to do with this routine...
def versionCompare(evr1, evr2):
    result = rpm.labelCompare(evr1, evr2)
    if (result < 0 ):
        return -1
    elif ( result == 0 ):
        return 0
    else:
        return 1
