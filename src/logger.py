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

MANDATORY = 0
VERBOSE   = 1
DEBUG     = 2
DEBUG2    = 3
TRIVIA    = 4 
TRACE     = 5    # at this level and above, log the source file and line #
MAX       = 10
    
logging_config = {
    'current_level': MANDATORY,
    'file': None,
    'prefix': "",
    'default_level': DEBUG2,
    }
    

def logconfig(current_level=None, file=None, prefix=None, indent=None,
           default_level=None):

    for item in logging_config.keys():
        ref = eval(item)        # is eval() expensive?
        if ref:                 # this test is to see if it was None
            if item in ['current_level', 'default_level']:
                logging_config[item] = int(ref)
            else:
                logging_config[item] = ref
      
def log(message, level=None):
    # This is very heavyweight - do we want "fast path" somehow?
    
    if level == None:
        level = logging_config['default_level']

    if level > logging_config['current_level']:
        return

    # Our timestamp format is:  MMM DD hh:mm:ss (this reproduces syslog format
    # in all but one way - the day is zero-padded, in syslog it's space-padded)
    tmp = time.strftime("%b %2d %H:%M:%S ", time.localtime(time.time()))
    
    # handle a common prefix attached to a series of logs
    if logging_config['prefix']:
        tmp = tmp + logging_config['prefix'] + ": "

    # If we are tracing, add that in
    if level >= TRACE:
        file, line, func, txt = traceback.extract_stack(None, 2)[0]
        tmp = tmp + '(%(file)s, %(func)s(), %(line)s): ' % locals()
        
    # Log the darn message
    tmp = tmp + message + "\n"
    logging_config['file'].write(tmp)
                           

def logException(level=MANDATORY):
    if level > logging_config['current_level']:
        return

    logfile = logging_config['file']

    # even though tracing is not normally done at lower logging levels,
    # we add trace data for exceptions
    file, line, func, txt = traceback.extract_stack(None, 2)[0]
    logfile.write('%s: EXCEPTION in %s, %s(), %s [%s]\n' %
                  (time.strftime("%b %2d %H:%M%S ", time.localtime(time.time())),
                   file, func, line, txt))
    
    (type, value, tb) = sys.exc_info()
    for line in traceback.format_exception(type, value, tb):
        logfile.write(line)

                  
def logfunc(args, level=DEBUG2):
    """ This logs a specific function call to the database. 

    If used at all logfunc should be the first statement after the
    docstring, if any.

    We ignore the 'self' local, if any, for methods.
    """

    if level > logging_config['current_level']:
        return

    # Add a timestamp first
    tmp = time.strftime("%b %2d %H:%M:%S ", time.localtime(time.time()))

    # handle a common prefix attached to a series of logs
    if logging_config['prefix']:
        tmp = tmp + logging_config['prefix'] + ": "

    file, line, func, txt = traceback.extract_stack(None, 2)[0]

    # Handle args=None and methods, which have a (sometimes huge) self.
    if args and args.has_key('self'):
        del args['self']

    # I'm tired of seeing the sysid. We need to know its there, not its 
    # value everywhere. This  requires discipline in the api functions to
    # always call it "sysid_string"
    if args and args.has_key('sysid_string'):
        args['sysid_string'] = '<sysid_string not logged>'

    tmp = tmp + '%(file)s:%(func)s(%(args)s)\n' % locals()

    logging_config['file'].write(tmp)


def _main():
    logconfig(current_level=MAX, file=sys.stderr, prefix="PRF", indent=1)

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
