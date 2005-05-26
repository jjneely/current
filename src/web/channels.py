import sys

from web import WebPageAbstract
from simpletal import simpleTAL, simpleTALES
from logger import *

class WebPage(WebPageAbstract):

    def listPackages(self, label):
        name = self.wdb.getChannelName(label)
        l = self.wdb.getPackages(label).dump()

        # Create the context that is used by the template
        context = simpleTALES.Context()
        context.addGlobal("title", "RPMS in channel %s" % name)

        context.addGlobal("rpm", l)

        html = self.build("channels.table.html", context)

        return html, 0


    def listChannels(self):
        chans = self.wdb.getChannels().dump()

        for c in chans:
            c['link'] = "channels.py?label=%s" % c['label']

        context = simpleTALES.Context()
        context.addGlobal("title", "Select Channel")
        context.addGlobal("channels", chans)

        html = self.build("channels.html", context)
        
        return html, 0
   
   
    def run(self):
        if self.fields.has_key("label"):
            return self.listPackages(self.fields['label'])
        else:
            return self.listChannels()
        
