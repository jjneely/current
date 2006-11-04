import xmlrpclib
import turbogears
import auth
import cherrypy.config
from turbogears import controllers

class SubDir(object):

    def __init__(self, api):
        self._api = api

class Policy(SubDir):

    @turbogears.expose(html="cwebapp.templates.policy")
    @auth.needsLogin
    def index(self, userInfo):
        myOU = self._api.policy.myOU(userInfo['session'])
        tree = self._api.policy.showTree(userInfo['session'])

        for row in tree:
            clients = self._api.policy.countProfilesOfOU(userInfo['session'],
                                                          row['ou_id'])
            row['num_clients'] = clients

        return dict(OU=myOU, tree=tree)

class Systems(SubDir):

    @turbogears.expose(html="cwebapp.templates.systems")
    @auth.needsLogin
    def index(self, userInfo):
        systems = self._api.cadmin.findProfile(userInfo['session'])
        return dict(systems=systems)

    @turbogears.expose(html="cwebapp.templates.systemDetail")
    @auth.needsLogin
    def details(self, userInfo, profileID):
        system = self._api.systems.systemDetail(userInfo['session'], 
                                                profileID)
        return dict(system=system)

class Channels(SubDir):

    @turbogears.expose(html="cwebapp.templates.channels")
    @auth.needsLogin
    def index(self, userInfo):
        channels = self._api.channels.listChannels(userInfo['session'])
        return dict(channels=channels)

    @turbogears.expose(html="cwebapp.templates.channelDetail")
    @auth.needsLogin
    def detail(self, userInfo, label):
        detail = self._api.channels.getChannelDetail(userInfo['session'],
                                                      label)
        return dict(channel=detail)

class Root(controllers.Root):

    def __init__(self):
        controllers.Root.__init__(self)
        self._api = xmlrpclib.Server(cherrypy.config.get("current"))

        self.systems = Systems(self._api)
        self.channels = Channels(self._api)
        self.policy = Policy(self._api)

    def doLoginCall(self, userid, password):
        return self._api.policy.login(userid, password)

    @turbogears.expose(html="cwebapp.templates.index")
    @auth.needsLogin
    def index(self, userInfo):
        print userInfo
        return dict(systemTotal=self._api.systems.systemCount(
                    userInfo['session']),
                    userID=userInfo['userid'])

    @turbogears.expose(html="cwebapp.templates.login")
    def login(self, redirect="/", message=None):
        auth.removeCookie()
        return dict(redirect=redirect, message=message)

