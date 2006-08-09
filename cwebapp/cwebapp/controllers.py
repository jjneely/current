import xmlrpclib
import turbogears
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

    @turbogears.expose(html="cwebapp.templates.index")
    def index(self):
        
        return dict(systemTotal=self.__api.systems.systemCount())
        
