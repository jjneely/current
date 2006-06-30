#!/usr/bin/python

""" Provides a global variable and factory function to get to the backend.

Copyright (c) 2002 Hunter Matthews    Distributed under GPL.

"""


from current.logger import *
from current.db.currentdb import CurrentDB

sdb = None

def selectBackend(config):
    """ Factory function to start the db type specified. """

    # We could do something fancy here, like 
    #   return globals()["%s_DB" % name]()
    # but for now, we keep it simple and stupid

    global sdb
    if config['db_type'] == 'postgres':
        from current.db import postgres
        sdb = postgres.PostgresDB(config)
    elif config['db_type'] == 'mysql':
        from current.db import mysql
        sdb = mysql.MysqlDB(config)
    elif config['db_type'] == 'pysqlite':
        from current.db import pysqlite
        sdb = pysqlite.PySqliteDB(config)
    else:
        raise Exception("unknown backend type")


## END OF LINE ##

