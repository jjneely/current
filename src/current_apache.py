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

from logger import *
import configure
import misc
#import packagedb
import auth

# Here are the recognized RHN api modules
__modules__ = ['errata', 'queue', 'registration', 'up2date', 'current']
import current
import errata
import queue
import registration
import up2date


def apacheLog(message, level='NOTICE'):
    """ log a message to the apache error log. pretties up an ugly api """

    aplevel = 'APLOG_' + level
    if hasattr(apache, aplevel):
        level = getattr(apache, aplevel)
    else:
        level = apache.APLOG_NOTICE
    apache.log_error(message, apache.APLOG_NOERRNO | level)


def init_backend():
    """ Initialize all the backend bits for current. 
    
    This gets run one time per apache process. 
    """

    apacheLog("Starting backend", 'NOTICE')

    # Config object
    apacheLog("Getting the server configuration", 'INFO')
    configure.config = configure.Config(configure.defaults)
    configure.config.load(apache=1)

    # Logging
    # We need logging running before we can init the database.
    logfile = configure.config['log_file']
    level = int(configure.config['log_level'])
    logconfig(level, open(logfile, "a", 0))
    apacheLog("Starting logging", 'INFO')
    apacheLog("Using current log %s" % logfile, 'INFO')

    log("Current v%s starting up" % configure.VERSION, MANDATORY)

    # Database 
    # In the future, the database may need to be up before auth
#     packagedb.db = packagedb.PackageDB()
#     for chan in configure.config['valid_channels']:
#         chan_info = configure.config['channels'][chan]
#         try:
#             packagedb.db.addChannel(chan_info)
#         except:
#             log("Error trying to add channel from %s" % chan_info['db_dir'], MANDATORY)

    # Authentication
    auth.authorize = auth.Authorization()


def accesshandler(req):
    """ Access Handler for mod_python.

    Performs the authentication/authorization using HTTP headers for 
    GET requests 
    """
    apacheLog("Inside the accesshandler", 'NOTICE')

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        init_backend()

    if 0:      # debugging code - leave this here
        apacheLog(req.uri)
        for key in req.headers_in.keys():
            apacheLog("headers_in[%s] == %s" %(key, req.headers_in[key]))
 
    # Now we can actually check on the  clients authorizations
    hi = auth.SysHeaders(req.headers_in)
    (valid, reason) = hi.isValid()
    if not valid:
        apacheLog("Request %s could not be authorized" % req.uri, 'NOTICE')
        apacheLog("Reason for failure was %s" % reason, 'NOTICE')
        return apache.HTTP_UNAUTHORIZED
    else:
        return apache.OK


def typehandler(req):
    """ Type Handler for mod_python.

    The packageList and the rpm headers are compressed. This
    handler sets the correct HTTP response headers if those are the
    requests we're handling.

    May be replaced in the future with a more advanced apache config.
    (See TODO)
    """

    apacheLog("Inside the typehandler", 'NOTICE')

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        init_backend()

    # setting headers creatively
    if string.find(req.uri, 'listPackages') > 0:
        # listPackages is both compressed, and has a different 
        # content_type than the others
        apacheLog('setting compressed headers')

        req.headers_out['Content-Encoding'] = 'x-gzip'
        req.headers_out['Content-Transfer-Encoding'] = 'binary'
        req.content_type = 'application/binary'
    else:
        # everything else is uncompressed, and is octet-stream
        apacheLog('setting normal headers')
        req.content_type = 'application/octet-stream'

    return apache.OK


def handler(req):
    """ The main handler function is used for all the POST requests """

    apacheLog("Inside the PythonHandler", 'NOTICE')

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        init_backend()

    if not req.method == 'POST':
        # This would be considered a Bad Thing...
        # FIXME: we need to log more stuff here, to debug the problem
        apacheLog("Unkown request type found!")
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
            logException()
            log ("Couldn't decode XMLRPC call.  We have problems.", DEBUG)
            return apache.HTTP_BAD_REQUEST
    
        try:
            # gen result
            log ('Requesting: %s' % method, DEBUG)
            log ('  with params = %s' % pprint.pformat(params), DEBUG2)
            # Fixme: need to pass req object here?
            result = callAPIMethod(method, params)
        except:
            logException()
            return apache.HTTP_BAD_REQUEST

        apacheLog('Result = %s' % pprint.pformat(result), 'NOTICE')
    
        return sendClientResult(req, result)


def loghandler(req):
    """ temp function for testing"""

    apacheLog("Inside the loghandler", 'NOTICE')

    # we assume that if the config object is there, all the init got done.
    if not configure.config:
        init_backend()

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
        log('Result is a Fault', DEBUG)
        req.headers_out.add('X-RHN-Fault-Code', str(result.faultCode))
        req.headers_out.add('X-RHN-Fault-String', base64.encodestring(result.faultString))
    else:
        log('Result is normal data: turn it into an XML chunk', DEBUG2)

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
        log('ERROR: Could not split method into module/function pair'
            % method, MANDATORY)
        log('  params were: %s' % pprint.pformat(params), MANDATORY)
        return xmlrpclib.Fault(1000, 'Method call not in expected format')

    (module, function) = string.split(method, '.', 1)
    # Is this a new or a known call?
    if not module in __modules__:
        # it's a whole new freaking module
        log('ERROR: New module called: %s with function %s'
            % (module, function), MANDATORY)
        log('  params were: %s' % pprint.pformat(params), MANDATORY)
        return xmlrpclib.Fault(1000, 'Module %s not recognized' % module)

    # This could blow up. but if it does, it's a server problem/bug
    tmp_api = eval('%s.__current_api__' % module)

    if not function in tmp_api:
        # known module, new function
        log('ERROR: New function called: module %s, function %s'
            % (module, function), MANDATORY)
        log('  params were: %s' % pprint.pformat(params), MANDATORY)

        return xmlrpclib.Fault(1000, 'Function %s not recognized'
                               % function)
    
    # OK, Everything should be good to go.
    log('module = %s' % module, TRIVIA)
    log('function = %s' % function, TRIVIA)
    log('params = %s' % pprint.pformat(params), TRACE)

    log('Dispatching: %s' % method, DEBUG)
    try:
        func = eval(method)
        result = apply(func, params)
        return result
    except TypeError, e:
        # We recognized the module and function, but mussed the arg count
        log('ERROR: Recognized function %s called with wrong arg count'
            % method, MANDATORY)
        logException()
        log('  params were: %s' % pprint.pformat(params), MANDATORY)
        return xmlrpclib.Fault(1000, 'Function %s called with wrong arg count'
                               % function)
    except Exception, e:
        # something totally bad happened.  :((
        log('ERROR: Recognized function %s blew up with undefined error'
            % method, MANDATORY)
        logException()
        log('  exception said: %s' % e, MANDATORY)
        log('  params were: %s' % pprint.pformat(params), MANDATORY)
        return xmlrpclib.Fault(1000, 'Function %s call blew up.  Bad week.'
                               % function)
