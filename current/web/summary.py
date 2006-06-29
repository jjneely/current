import sys

from web import WebPageAbstract
from simpletal import simpleTAL, simpleTALES
from logger import *

class WebPage(WebPageAbstract):

    def run(self):
        context = simpleTALES.Context()
        return self.build("summary.html", context), 0

