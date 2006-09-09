""" Implementation of the MySQL backend for Current"""

import MySQLdb

from current.db.currentdb import specificDB
from current.logger import *
from current.db.mysql import schema

class MysqlDB(specificDB):
    
    def __init__(self, config):
        self.conn = None
        self.cursor = None

        self.config = config
        

    def __del__(self):
        self.disconnect()


    def getConnection(self):
        if self.conn:
            return self.conn
        
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
        
        return self.conn


    def getCursor(self):
        if self.conn == None:
            self.getConnection()

        if self.cursor == None:
            self.cursor = self.conn.cursor()
            # This sets this thread so that it will see data committed
            # by other apache processes
            self.cursor.execute("""SET SESSION TRANSACTION ISOLATION LEVEL 
                                   READ COMMITTED""")

        return self.cursor


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

