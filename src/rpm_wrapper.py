""" Wrapper module around rpmlib.

Because the rpm module has so many quirks that may affect current, we 
encapsulate all the direct rpm interactions in this module, so that the 
backends and other code see a single, sane, consistent interface.

Current has also had several rpm related bugs, so bug fixes here will 
automatically fix all the backends.

"""

import os
import os.path
import rpm


def getRpmInfo(pathname):
    """ Get all the data out of an rpm.

    This is a single interface to get all the needed information out of a
    single rpm. This means that all the backends will be using a common 
    source for rpm data. A number of past current bugs were in this part
    of the code, and a single source ensures any bug fix here will show
    up in all the backends.

    Returns a dict
    """

    (hdr, isSource) = _getHeaderFromFilename(pathname)

    info = {}
    info['pathname'] = pathname

    # grab the size of the file itself, not the installed size
    info['size'] = str(os.stat(pathname)[stat.ST_SIZE])

    # Basic package information
    info['name'] = hdr[rpm.RPMTAG_NAME]
    info['version'] = hdr[rpm.RPMTAG_VERSION]
    info['release'] = hdr[rpm.RPMTAG_RELEASE]
    info['arch'] = hdr[rpm.RPMTAG_ARCH]

    # Library hands back an int or None - we want a string
    epoch = hdr[rpm.RPMTAG_EPOCH]
    if epoch == None:
        epoch = ''
    else:
        epoch = str(epoch)
    info['epoch'] = epoch

    # The files index is a simple, possibly multi-valued list
    info['dep_files'] = hdr[rpm.RPMTAG_FILENAMES]
    
    # The provides are just plain mean.
    # complex, multi-valued list. You actually have to look at
    # RPMTAG_PROVIDENAME[x] -> RPMTAG_PROVIDEFLAGS[x] 
    #   -> RPMTAG_PROVIDEVERSIONS[x] for each x in the 3 lists.
    info['dep_provides'] = []

    # We make some temporary names to shorten the code. A little.
    pnames = hdr[rpm.RPMTAG_PROVIDENAME]
    pvers = hdr[rpm.RPMTAG_PROVIDEVERSION]
    pflags = hdr[rpm.RPMTAG_PROVIDEFLAGS] 

    # BUGFIX: rpm doesn't make PROVIDEFLAGS a list if there is only
    # one. Stupid library.
    if pnames != None:
        if type(pflags) != types.ListType:
            pflags = [pflags]
        if type(pvers) != types.ListType:
            pvers = [pvers]

    for i in range(len(pnames)):
        info['dep_provides'].append([pnames[i], str(pflags[i]), pvers[i]])
        
    # Now we have to do the same for obsoletes, if there are any
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

    # Add the rpm -> srpm link
    info['srpm'] = hdr[rpm.RPMTAG_SOURCERPM]

    # The backends must store the header _somewhere_.
    info['hdr'] = hdr
    
    return info


def _getHeaderFromFilename(pathname, binary=1):
    """ Open a pathname as an rpm, and retrive the header from it. """

    try:
        fd = os.open(pathname, os.O_RDONLY)
        (header, isSource) = rpm.headerFromPackage(fd)
        os.close(fd)

    except:
#        logException()
        print "Warning: Could not open package %s" % pathname
        return (None, None)
        
    if header == None:
        ## FIXME, we should have an error stream or callback or
        ## something - this is crude.
        print "Warning: Could not read package %s" % pathname
        return (None, None)

    # FIXME: possibly, we should do more than just log the infraction
    # These infractions will be handled in the calling routines, so just
    # log it at the debug level and go on with life.
    if isSource and binary:
        # FIXME: need something better here
        print "Warning: source rpm %s found in bin dir." % pathname
    elif ((not isSource) and (not binary)):
        # Opposite of previous test - expecting source rpm, found binary
        print "Warning: binary rpm %s found in src dir." % pathname
    else:
        return (header, isSource)

