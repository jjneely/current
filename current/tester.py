#! /usr/bin/python

from RPM import *
#import rpm_wrapper
import os
import sys
import types
import pprint

for file in ['/export/trees/realmlinux-ws4/SRPMS/nmh-1.0.4-20.src.rpm']:
    h = Header(file)

#    pprint.pprint(dir(h))
    print file
    print '   SOURCEPACKAGE     %s' % h[SOURCEPACKAGE],
    print type(h[SOURCEPACKAGE])
    assert type(h[SOURCEPACKAGE]) == int, "tester.py, type violation"

    print '   ARCH              %s' % h[ARCH]

    print '   CT_FILESIZE       %s' % h[CT_FILESIZE],
    print type(h[CT_FILESIZE])
    assert type(h[CT_FILESIZE]) == long

    print '   PROVIDENAME       %s' % h[PROVIDENAME]
    assert type(h[PROVIDENAME]) == list
    #assert type(h[PROVIDENAME][0]) == str

    print '   PROVIDEFLAGS      %s' % h[PROVIDEFLAGS]
#    print '   rpm thinks        %s' % h.hdr[rpm_wrapper.rpm.RPMTAG_PROVIDEFLAGS]
    assert type(h[PROVIDEFLAGS]) == list
    #assert type(h[PROVIDEFLAGS][0]) == int

    print '   PROVIDEVERSION    %s' % h[PROVIDEVERSION]
    assert type(h[PROVIDEVERSION]) == list
    #assert type(h[PROVIDEVERSION][0]) == str

    print '   CT_PROVIDES       %s' % h[CT_PROVIDES]
    assert type(h[PROVIDES]) == list

    print '   CT_OBSOLETES      %s' % h[CT_OBSOLETES]
#    assert type(h[OBSOLETES]) == list 
    
    print '   NAME              %s' % h[NAME]
    assert type(h[NAME]) == str

    print '   VERSION           %s' % h[VERSION]
    assert type(h[VERSION]) == str

    print '   EPOCH             %s' % h[EPOCH]

    print '   CT_PATHNAME       %s' % h[CT_PATHNAME]

#    sys.exit(1)

    
    print 

