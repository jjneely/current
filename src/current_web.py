from mod_python import apache
from sessions import *
from logger import *
from current_apache import init_backend
import configure
import db

def handler(req):
    if not configure.config:
        ret = init_backend()
        if ret:
            return apache.HTTP_INTERNAL_SERVER_ERROR
        
    log("Inside Current Web handler", DEBUG)

    req.content_type = "text/plain"

    sess = CookieSession(req)
    if sess.isNew():
        sess['userid'] = "foobar"
        sess.save()
        req.write("New session!\n")
    else:
        sess.save()
        req.write("Old session, userid = %s" % sess['userid'])
    
    req.write("sid = %s\n" % sess.sid)

    return apache.OK


