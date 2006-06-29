""" current module implementing apache/mod_python calls.
    
ModPython makes calls to various handler methods, instead of using a single
main() function. Those handlers are here, with their support code. Current
itself has no main.

accesshandler() and typehandler() are used during GET requests. handler()
does all the processing needed for POST requests. init_*() starts up the 
various bits of current during the first call. 

Copyright 2001, 2002 Hunter Matthews
Copyright 2002 John Berninger

This software may be freely redistributed under the terms of the GNU Public
License (GPL) v2.

See http://www.biology.duke.edu/computer/unix/current
"""

import base64
import xmlrpclib
import string
import pprint
import types
import sys

from mod_python import apache

from current.logger import *
from current.exception import CurrentException
from current import configure
from current import auth
from current import db
from current import api

# Here are the recognized RHN api modules
__modules__ = ['errata', 'queue', 'registration', 'up2date', 'cadmin', 'applet']

def apacheLog(message, level='NOTICE'):
    """ log a message to the apache error log. pretties up an ugly api """

    aplevel = 'APLOG_' + level
    if hasattr(apache, aplevel):
        level = getattr(apache, aplevel)
    else:
        level = apache.APLOG_NOTICE
    apache.log_error(message, apache.APLOG_DEBUG)


def init_backend():
    """ Initialize all the backend bits for current. 
    
    This gets run one time per apache process. 
    """

    apacheLog("Starting backend", 'NOTICE')

    # Config object
    apacheLog("Getting the server configuration", 'INFO')
    configure.config = configure.Config(configure.defaults)
    configure.config.load()

    # Logging
    # We need logging running before we can init the database.
    logfile = configure.config['log_file']
    level = int(configure.config['log_level'])

    # This is a common error - The user apache runs as either can't create
    # or can't append to the current.log file.
    try:
        logconfig(level, logfile)
    except IOError, e:
        apacheLog("Cannot open the %s log file. Usually a permissions problem." % logfile, 'ALERT')
        apacheLog("This is going to hinder all current operation - please fix", 'ALERT')
        return 1

    apacheLog("Starting logging", 'INFO')
    apacheLog("Using current log %s" % logfile, 'INFO')

    log("Current v%s starting up" % configure.VERSION, MANDATORY)

    # Setup the database connection
    # In the future, the database may need to be up before auth
    try:
        db.selectBackend(configure.config)
    except Exception, e:
        log("Error initializing data base!  Current will not function",
                MANDATORY)
        logException()
        return 1

    # Authentication
    auth.authorize = auth.Authorization()

    return 0


def accesshandler(req):
    """ Access Handler for mod_python.

    Performs the authentication/authorization using HTTP headers for 
    GET requests 
    """

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        ret = init_backend()
        if ret:
            # Backend failed to start up
            return apache.HTTP_INTERNAL_SERVER_ERROR

    # debugging code - leave this here
    log("Inside Current accesshandler", TRIVIA)
    log(req.uri, DEBUG2)
    for key in req.headers_in.keys():
        #if key[0:5] in ["x-rhn", "x-up2"]:
        log("headers_in[%s] == %s" %(key, req.headers_in[key]), TRACE)

    try:
        # Now we can actually check on the  clients authorizations
        hi = auth.SysHeaders(req.headers_in)
        (valid, reason) = hi.isValid()
    except CurrentException, e:
        log("ERROR: A CurrentException was raised -- in accesshandler().",
            MANDATORY)
        logException()
        return apache.HTTP_INTERNAL_SERVER_ERROR
    except Exception, e:
        log("ERROR: accesshandler() blew up with undefined error",
            MANDATORY)
        logException()
        return apache.HTTP_INTERNAL_SERVER_ERROR
                        
    if not valid:
        log("Request %s could not be authorized" % req.uri, VERBOSE)
        log("Reason for failure was %s" % reason, VERBOSE)
        return apache.HTTP_UNAUTHORIZED
    else:
        return apache.OK


def handler(req):
    """ The main handler function is used for all the POST requests """

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        ret = init_backend()
        if ret:
            # Backend failed to start up
            return apache.HTTP_INTERNAL_SERVER_ERROR

    log("Inside Current main hander", DEBUG)

    if req.method == 'GET':
        return apache.DECLINED

    if not req.method == 'POST':
        # This would be considered a Bad Thing...
        # FIXME: we need to log more stuff here, to debug the problem
        log("Don't know how to handle this request type: %s" % req.method, DEBUG)
        return apache.HTTP_BAD_REQUEST
    else:
        try:
            #get the arguments
            data = req.read(int(req.headers_in['content-length']))
            params, method = xmlrpclib.loads(data)
            params = list(params)
        except:
            # had a problem with the xmlrpc call...
            log ("Couldn't decode XMLRPC call.", VERBOSE)
            logException()
            return apache.HTTP_BAD_REQUEST
    
        # gen result
        log ('Requesting: %s' % method, DEBUG)
        log ('  with params = %s' % pprint.pformat(params), DEBUG2)
        # Fixme: need to pass req object here?
        result = callAPIMethod(method, params)

        log('API Result = %s' % pprint.pformat(result), DEBUG2)
    
        return sendClientResult(req, result)


def loghandler(req):
    """ temp function for testing"""

    apacheLog("Inside the loghandler", 'NOTICE')

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        ret = init_backend()
        if ret:
            # Backend failed to start up
            return apache.HTTP_INTERNAL_SERVER_ERROR

    for key in req.headers_out.keys():
        apacheLog("headers_out[%s] == %s" %(key, req.headers_out[key]))

    apacheLog(req.uri)
    apacheLog(req.content_type)

    return apache.OK


def sendClientResult(req, result):
    """ Send the results of an up2date API method call back to the client.

    The result might be an exception or valid (xmlrpc) data.

    """

    data = ''                           # start off with nothing

    if isinstance(result, xmlrpclib.Fault):
        log("Fault: %s" % str(result), VERBOSE)
        req.headers_out.add('X-RHN-Fault-Code', str(result.faultCode))
        req.headers_out.add('X-RHN-Fault-String', string.strip(base64.encodestring(result.faultString)))
        data = xmlrpclib.dumps(result, methodresponse=1)
    else:
        log('Result is normal data: turn it into an XML chunk', DEBUG)

        # Force data to be encapsulated in a tuple.
        # NOTE: thats NOT at all what the tuple() builtin does.
        if type(result) != type(()):
            data = (result,)
        else:
            data = result
        data = xmlrpclib.dumps(data, methodresponse=1)

    # All POST results are 'text/xml' with the length set, regardless of 
    # a normal or error condition return.
    req.headers_out.add('Content-type', 'text/xml')
    req.headers_out.add('Content-length', str(len(data)))

    # Define out Capabilities
    # XXX: Sane way to do this?
    caps = 'registration.extendedPackageProfile(1)=1'
    req.headers_out.add('X-RHN-Server-Capability', caps)

    req.send_http_header()
    req.write(data)
    log('Data sent.', TRACE)
    log('sendClientResult() finished', DEBUG)

    return apache.OK


def callAPIMethod(method, params):
    """ Call one of the up2date API functions.

    This function very carefully breaks down the API call, 
    dispatches the call, and then returns the result. Its 90% error
    handling.

    """

    global __modules__
    if not string.count(method, '.'):
        log('Could not split method into module/function pair'
            % method, DEBUG)
        log('  params were: %s' % pprint.pformat(params), DEBUG2)
        return xmlrpclib.Fault(1000, 'Method call not in expected format')

    log('method = %s' % method, DEBUG)
    (module, function) = string.split(method, '.', 1)
    # Is this a new or a known call?
    if not module in __modules__:
        # it's a whole new freaking module
        log('ERROR: New module called: %s with function %s'
            % (module, function), MANDATORY)
        log('  params were: %s' % pprint.pformat(params), DEBUG2)
        return xmlrpclib.Fault(1000, 'Module %s not recognized' % module)

    # This could blow up. but if it does, it's a server problem/bug
    tmp_api = api.__getattribute__(module).__current_api__
    #tmp_api = eval('%s.__current_api__' % module)

    if not function in tmp_api:
        # known module, new function
        log('ERROR: New function called: module %s, function %s'
            % (module, function), MANDATORY)
        log('  params were: %s' % pprint.pformat(params), DEBUG2)

        return xmlrpclib.Fault(1000, 'Function %s not recognized'
                               % function)
    
    # OK, Everything should be good to go.
    log('module = %s' % module, TRIVIA)
    log('function = %s' % function, TRIVIA)
    log('params = %s' % pprint.pformat(params), TRACE)

    log('Dispatching: %s' % method, DEBUG)
    try:
        func = api.__getattribute__(module).__getattribute__(function)
        #func = eval(method)
        result = apply(func, params)
        return result
    except TypeError, e:
        # We recognized the module and function, but mussed the arg count
        log('ERROR: Recognized function %s called with wrong arg count '
            'or other TypeError exception occured' % method, MANDATORY)
        logException()
        log('  params were: %s' % pprint.pformat(params), DEBUG2)
        return xmlrpclib.Fault(1000, 'Function %s called with wrong arg count'
                               % function)
        
    except CurrentException, e:
        # Something bad happened that we cought and need to tell the user
        log("ERROR: A CurrentException was raised -- alert user.", 
            MANDATORY)
        logException()
        log('  params were: %s' % pprint.pformat(params), DEBUG2)
        return xmlrpclib.Fault(1000, str(e))
    
    except Exception, e:
        # something totally bad happened.  :((
        log('ERROR: Recognized function %s blew up with undefined error'
            % method, MANDATORY)
        logException()
        log('  params were: %s' % pprint.pformat(params), DEBUG2)
        return xmlrpclib.Fault(1000, 'Function %s call blew up.  Bad week.'
                               % function)
