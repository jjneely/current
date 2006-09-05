import cherrypy
import pickle

CookieName = 'CurrentWebCookie'

def getCurrentSid():
    try:
        blob = cherrypy.request.simpleCookie[CookieName].value
    except KeyError:
        return None

    dict = pickle.loads(blob)

    return dict

def setCurrentSid(session, userid, name):
    dict = {}
    dict['session'] = session
    dict['userid'] = userid
    dict['name'] = name
    cherrypy.response.simpleCookie[CookieName] = pickle.dumps(dict)

def needsLogin(fn):
    def _wrapper(*args, **kwargs):
        userInfo = getCurrentSid()
        if userInfo == None:
            # User is not logged in
            try:
                userid = kwargs['userid']
                password = kwargs['password']
            except KeyError:
                # Not a login attempt
                # Make user login
                params = {'redirect':'/index', 'message':'You must login.'}
                raise cherrypy.InternalRedirect('/login', params)

            # Authenticate the user by calling into Current
            sid = cherrypy.root.doLoginCall(userid, password)
            if sid['code'] != 0:
                # Bad attempt
                # XXX: Inital login?
                params = {'redirect':'/index', 
                          'message':'Invaild user name or password.'}
                raise cherrypy.InternalRedirect('/login', params)

            setCurrentSid(sid['session'], userid, "Jane Smith")
            userInfo = getCurrentSid()

        # Patch up arguments, take out login/password, and add a dict
        # describing the user
        kwargs['userInfo'] = userInfo
        for a in ['userid', 'login', 'password']:
            if kwargs.has_key(a):
                del kwargs[a]
        return fn(*args, **kwargs)
    return _wrapper

