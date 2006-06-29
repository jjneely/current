from mod_python import apache
from mod_python import util
from current.sessions import *
from current.logger import *
from current.current_apache import init_backend
from current import configure
from current import db
import os.path
from current import web
import traceback
import sys
import string
import time

def handler(req):
    if not configure.config:
        ret = init_backend()
        log("Web handler: Init Backend!", DEBUG)
        if ret:
            return apache.HTTP_INTERNAL_SERVER_ERROR
        
    log("Inside Current Web handler", DEBUG)
    req.content_type = "text/html"

    t = time.time()
    sess = CookieSession(req)
    if sess.isNew():
        sess['userid'] = "foobar"
    
    file = os.path.basename(req.uri)
    mod = file.split('.')[0]
    if mod in ["", "current"]:
        # Request without specific python file to run.  Give user summary
        mod = "summary"
        
    if mod in web.modules:
        try:
            page = web.modules[mod].WebPage(configure.config,
                                            sess,
                                            util.FieldStorage(req))
            s, ret = page.run()
            sess.save()
            req.write(s)
        except Exception, e:
            # show exception on the browser
            req.content_type = "text/plain"
            req.write("A Python Exception has Occured:\n\n")
            text = traceback.format_exception(sys.exc_type,
                                              sys.exc_value,
                                              sys.exc_traceback)
            req.write(string.join(text, '\n'))

        req.write("Time: %s\n" % str(time.time()-t))
        return apache.OK
            
    # Okay, we didn't find any code to run based of what was requested
    return apache.HTTP_NOT_FOUND


