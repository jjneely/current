#! /usr/bin/python
"""
A module for generating pretty logging/debugging information from a program.

NOTE: As this module will typically be imported via 
from logger import *
we take pains to polute the namespace as little as possible.

"""


import sys
import traceback
import time
import os
import logging

MANDATORY = CRITICAL = 100
ERROR     = 60
VERBOSE = WARNING  = 50
DEBUG     = 40
DEBUG2    = 30
TRIVIA    = 20
TRACE     = 10    # at this level and above, log the source file and line #
MAX       = 1
    

def logconfig(level, file):
    "Initialize the python logger for Current."   
    logger = logging.getLogger()

    # Levels
    logging.addLevelName(100, "CRITICAL")
    logging.addLevelName(60, "ERROR")
    logging.addLevelName(50, "WARNING")
    logging.addLevelName(40, "DEBUG")
    logging.addLevelName(30, "DEBUG2")
    logging.addLevelName(20, "TRIVIA")
    logging.addLevelName(10, "TRACE")
    logging.addLevelName(0, "")
    
    handler = logging.FileHandler(file)
    # Time format: Jun 24 10:16:54
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',
                                  '%b %2d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    logger.info("Logging initialized.")
      
def log(a, b=WARNING):
    logger = logging.getLogger()

    # *sigh* Current has always used (message, level) while python's
    # logging module uses (level, message)....just make it up
    if isinstance(a, int):
        level = a
        message = b
    else:
        level = b
        message = a
    
    # If we are tracing, add that in
    if level <= TRACE:
        file, line, func, txt = traceback.extract_stack(None, 2)[0]
        trace = '(File: %s, Method: %s(), Line: %s) ' % (file, func, line)
        message = trace + message
        
    # Log the darn message
    logger.log(level, message)

def logException(level=CRITICAL):
    logger = logging.getLogger()
    if level < logger.getEffectiveLevel():
        return

    logfile = logging_config['file']

    # even though tracing is not normally done at lower logging levels,
    # we add trace data for exceptions
    file, line, func, txt = traceback.extract_stack(None, 2)[0]
    trace = 'EXCEPTION (File: %s, Method: %s(), Line: %s): [%s]\n' % \
            (file, func, line, txt)
    logger.log(level, trace)
    
    (type, value, tb) = sys.exc_info()
    for line in traceback.format_exception(type, value, tb):
        logger.log(level, line)

                  
def logfunc(args, level=DEBUG2):
    """ This logs a specific function call to the database. 

    If used at all logfunc should be the first statement after the
    docstring, if any.

    We ignore the 'self' local, if any, for methods.
    """

    logger = logging.getLogger()
    if level > logger.getEffectiveLevel():
        return

    file, line, func, txt = traceback.extract_stack(None, 2)[0]

    # Handle args=None and methods, which have a (sometimes huge) self.
    if args and args.has_key('self'):
        del args['self']

    # I'm tired of seeing the sysid. We need to know its there, not its 
    # value everywhere. This  requires discipline in the api functions to
    # always call it "sysid_string"
    if args and args.has_key('sysid_string'):
        args['sysid_string'] = '<sysid_string not logged>'

    message = '%(file)s:%(func)s(%(args)s)\n' % locals()

    logger.log(level, message)

def _main():
    logconfig(MAX, "/tmp/logger")

    def testfunc(a, b, c):
        """ This is a docstring """
        logfunc(locals())
        x = 1
        y = "my name is mudd"
        z = None
        logfunc(locals())

    class testclass:
        def testmethod(self, m, n, o):
            """ docstring again """
            logfunc(locals())

    log("Here", TRACE)
    log("And here")

    testfunc("Hunter", 55, [None, 5, 50])
    obj = testclass()
    obj.testmethod('a stitch', 'in time', 'saves nine')

    log("Last time")

            
if __name__ == '__main__':
    _main()
                      
## END OF LINE ##
