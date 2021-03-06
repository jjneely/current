""" Implementation of the MySQL backend for Current"""

import MySQLdb

from current.db.currentdb import specificDB
from current.logger import *
from current.db.mysql import schema

# Grrr...  MySQL-Python doesn't support reconnecting
class Connection(object):

    def __init__(self, sdb):
        self.sdb = sdb

    def __getattr__(self, name):
        if self.sdb.conn == None:
            self.sdb.getConnection()

        return getattr(self.sdb.conn, name)

class Cursor(object):

    def __init__(self, sdb):
        self.sdb = sdb
        self.__method = None

    def __getattr__(self, name):
        if self.sdb.cursor == None:
            self.sdb.getCursor()

        if name == "execute":
            self.__method = name
            return self.__wrapper
        else:
            return getattr(self.sdb.cursor, name)

    def __wrapper(self, *args, **kwargs):
        try:
            func = getattr(self.sdb.cursor, self.__method)
        except TypeError:
            log(CRITICAL, "BUG: MySQL cursor wrapper blew up.")
            raise

        try:
            return func(*args, **kwargs)
        except MySQLdb.OperationalError, e:
            log(DEBUG2, "OperationalError: e.args = %s" % str(e.args))
            if e.args[0] in (2006, 2013):
                log(VERBOSE, "Forcing reconnect to MySQL database")
                self.sdb.conn = None
                self.sdb.cursor = None
                self.sdb.getCursor()
                func = getattr(self.sdb.cursor, self.__method)
                return func(*args, **kwargs)
            else:
                raise

class MysqlDB(specificDB):
    
    def __init__(self, config):
        self.conn = None
        self.wrappedConn = None

        self.cursor = None
        self.wrappedCursor = None

        self.config = config
        

    def __del__(self):
        self.disconnect()


    def getConnection(self):
        if self.conn != None:
            return self.wrappedConn
        
        try:
            log("Obtaining connection", TRACE)
            self.conn = MySQLdb.connect(user=self.config['db_user'], 
                                     passwd=self.config['db_pass'], 
                                     host=self.config['db_host'], 
                                     db=self.config['db_name'])
            log("Connected via user/password", TRACE)
        except Exception, e:
            log("Could not get DB connection! (%s)" % str(e), MANDATORY)
            # Do something useful here?
            raise
        
        self.wrappedConn = Connection(self)
        return self.wrappedConn


    def getCursor(self):
        if self.conn == None:
            self.getConnection()

        if self.cursor == None:
            self.cursor = self.conn.cursor()
            self.wrappedCursor = Cursor(self)
            # This sets this thread so that it will see data committed
            # by other apache processes
            self.cursor.execute("""SET SESSION TRANSACTION ISOLATION LEVEL 
                                   READ COMMITTED""")

        return self.wrappedCursor


    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None


    def initdb(self):
        for x in schema.INITDB.split(';'):
            if x not in ["", "\n"]:
                self.cursor.execute(x+";")
        
        self.conn.commit()
        log("Database table create commited.  Initdb done.", TRACE)

