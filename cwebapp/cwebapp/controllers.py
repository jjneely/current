import xmlrpclib
import turbogears
import auth
import cherrypy.config
from turbogears import controllers

class Systems(object):

    def __init__(self, api):
        self.__api = api

    @turbogears.expose(html="cwebapp.templates.systems")
    @auth.needsLogin
    def index(self, userInfo):
        systems = self.__api.cadmin.findProfile(userInfo['session'])
        return dict(systems=systems)

    @turbogears.expose(html="cwebapp.templates.systemDetail")
    @auth.needsLogin
    def details(self, userInfo, profileID):
        system = self.__api.systems.systemDetail(userInfo['session'], 
                                                profileID)
        return dict(system=system)

class Channels(object):

    def __init__(self, api):
        self.__api = api

    @turbogears.expose(html="cwebapp.templates.channels")
    @auth.needsLogin
    def index(self, userInfo):
        channels = self.__api.channels.listChannels(userInfo['session'])
        return dict(channels=channels)

    @turbogears.expose(html="cwebapp.templates.channelDetail")
    @auth.needsLogin
    def detail(self, userInfo, label):
        detail = self.__api.channels.getChannelDetail(userInfo['session'],
                                                      label)
        return dict(channel=detail)

class Root(controllers.Root):

    def __init__(self):
        controllers.Root.__init__(self)
        self.__api = xmlrpclib.Server(cherrypy.config.get("current"))

        self.systems = Systems(self.__api)
        self.channels = Channels(self.__api)

    def doLoginCall(self, userid, password):
        return self.__api.cadmin.login(userid, password)

    @turbogears.expose(html="cwebapp.templates.index")
    @auth.needsLogin
    def index(self, userInfo):
        print userInfo
        return dict(systemTotal=self.__api.systems.systemCount(
                    userInfo['session']),
                    userID=userInfo['userid'])

    @turbogears.expose(html="cwebapp.templates.login")
    def login(self, redirect="/", message=None):
        auth.removeCookie()
        return dict(redirect=redirect, message=message)

