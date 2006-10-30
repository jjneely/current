from sqlobject import *

from turbogears.database import PackageHub

hub = PackageHub("cwebapp")
__connection__ = hub

# class YourDataClass(SQLObject):
#     pass

