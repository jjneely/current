#!/usr/bin/python

""" Provides a global variable and factory function to get to the backend.

Copyright (c) 2002 Hunter Matthews    Distributed under GPL.

"""


from current.logger import *
from current.db.currentdb import *

# This single global insures that all anyone else needs to know is 
# I hate doubled names like this, but I couldn't think of anything else
# that was short.
db = None
sdb = None

def selectBackend(config):
    """ Factory function to start the db type specified. """

    # We could do something fancy here, like 
    #   return globals()["%s_DB" % name]()
    # but for now, we keep it simple and stupid

    global db, sdb
    if config['db_type'] == 'postgres':
        import postgres
        sdb = postgres.PostgresDB(config)
    elif config['db_type'] == 'mysql':
        import mysql
        sdb = mysql.MysqlDB(config)
    elif config['db_type'] == 'pysqlite':
        import pysqlite
        sdb = pysqlite.PySqliteDB(config)
    else:
        raise Exception("unknown backend type")

    db = CurrentDB(config)


## END OF LINE ##

