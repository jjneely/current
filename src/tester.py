#! /usr/bin/python

from RPM import *
#import rpm_wrapper
import os
import sys
import types

os.chdir('/scratch/RedHat/RPMS')
for file in os.listdir('.'):
    h = Header(file)
    print file
    print '   SOURCEPACKAGE     %s' % h[SOURCEPACKAGE]
    assert type(h[SOURCEPACKAGE]) == int

    print '   CT_FILESIZE       %s' % h[CT_FILESIZE]
#    print type(h[CT_FILESIZE])
    assert type(h[CT_FILESIZE]) == str

    print '   PROVIDENAME       %s' % h[PROVIDENAME]
    assert type(h[PROVIDENAME]) == list
    assert type(h[PROVIDENAME][0]) == str

    print '   PROVIDEFLAGS      %s' % h[PROVIDEFLAGS]
#    print '   rpm thinks        %s' % h.hdr[rpm_wrapper.rpm.RPMTAG_PROVIDEFLAGS]
    assert type(h[PROVIDEFLAGS]) == list
    assert type(h[PROVIDEFLAGS][0]) == int

    print '   NAME              %s' % h[NAME]
    assert type(h[NAME]) == str

    print '   VERSION           %s' % h[VERSION]
    assert type(h[VERSION]) == str

#    sys.exit(1)

    
    print 

