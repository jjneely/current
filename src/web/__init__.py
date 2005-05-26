from simpletal import simpleTAL, simpleTALES

import db.web
import StringIO
import os.path

class WebPageAbstract(object):

    templateDir = None

    def __init__(self, config, session, fs):
        self.session = session
        self.fields = fs
        self.config = config
        self.templateDir = config['template_dir']

        self.wdb = db.web.WebDB()

        self.defaultMenu = []
        self.defaultMenu.append({'link': "/current/summary.py",
                                 'name': "Summary"})
        self.defaultMenu.append({'link': "/current/channels.py",
                                 'name': "Channels"})


    def build(self, file, context, menus=None):
        """Build the TAL templates and return a string with the HTML
           markup."""
        
        if menus == None:
            menus = self.defaultMenu
            
        f = os.path.join(self.templateDir, "template.html")
        fd = open(f)
        cssTemplate = simpleTAL.compileHTMLTemplate(fd)
        fd.close()

        f = os.path.join(self.templateDir, file)
        templateFile = open(f)
        template = simpleTAL.compileHTMLTemplate(templateFile)
        templateFile.close()

        buff = StringIO.StringIO()
        
        context.addGlobal("currentContent", template)
        context.addGlobal("currentMenus", menus)
        context.addGlobal("currentVersion", 
                          "Current Version " + self.config['version'])
        cssTemplate.expand(context, buff)

        return buff.getvalue()

        
    def run(self):
        return "No Page", 0


import channels
import summary

modules = {}
modules['channels'] = channels
modules['summary']  = summary
