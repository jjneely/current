""" Implementation of the PostgreSQL backend for Current"""

import pgdb

from db.currentdb import specificDB
from logger import *

import schema

class PostgresDB(specificDB):
    
    def __init__(self, config):
        self.conn = None
        self.cursor = None

        self.config = config
        

    def __del__(self):
        self.disconnect()


    def getConnection(self):
        log("Obtaining connection", TRACE)
        if self.conn:
            log("Connection already exists!", TRACE)
            return
        try:
            self.conn = pgdb.connect(user=self.config['db_user'], 
                                     password=self.config['db_pass'], 
                                     host=self.config['db_host'], 
                                     database=self.config['db_name'])
            log("Connected via user/password", TRACE)
        except Exception, e:
            log("Could not get DB connection!", MANDATORY)
            logexception()
            # Do something useful here?
            raise
        
        return self.conn


    def getCursor(self):
        if self.cursor == None:
            self.cursor = self.conn.cursor()

        return self.cursor


    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None


    def initdb(self):
        self.cursor.execute(schema.INITDB)
        self.conn.commit()
        log("Database table create commited.  Initdb done.", TRACE)


