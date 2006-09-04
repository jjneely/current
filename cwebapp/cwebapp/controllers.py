import xmlrpclib
import turbogears
import auth
import cherrypy.config
from turbogears import controllers

class Systems(object):

    def __init__(self, api):
        self.__api = api

    @turbogears.expose(html="cwebapp.templates.systems")
    def index(self):
        profiles = self.__api.cadmin.findProfile()
        return dict(profiles=profiles)

class Root(controllers.Root):

    def __init__(self):
        controllers.Root.__init__(self)
        self.__api = xmlrpclib.Server(cherrypy.config.get("current"))

        self.systems = Systems(self.__api)

    def doLoginCall(self, userid, password):
        return self.__api.cadmin.login(userid, password)

    @turbogears.expose(html="cwebapp.templates.index")
    @auth.needsLogin
    def index(self, userInfo):
        return dict(systemTotal=self.__api.systems.systemCount(),
                    userID=userInfo['userid'])

    @turbogears.expose(html="cwebapp.templates.login")
    def login(self, redirect="/", message=None):
        return dict(redirect=redirect, message=message)

