#!/usr/bin/python

""" Provides a global variable and factory function to get to the backend.

Copyright (c) 2002 Hunter Matthews    Distributed under GPL.

"""


#from logger import *

# This single global insures that all anyone else needs to know is 
# db.conn
conn = None


def selectBackend(db_type):
    """ Factory function to start the db type specified. """

    # We could do something fancy here, like 
    #   return globals()["%s_DB" % name]()
    # but for now, we keep it simple and stupid

    global conn
    if db_type == 'shelf':
        import shelf
        conn = shelf.CurrentDB()
    elif db_type == 'postgres':
        import postgres
        conn = postgres.PostgresDB()
    elif db_type == 'sqlite':
        import sqlite
        conn = sqlite.SqliteDB()
    else:
        raise Exception("unknown backend type")


## END OF LINE ##

