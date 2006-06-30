""" An implementation of currents backend as an sqlite database.

   Sqlite is a single file 'embedded' database that supports nearly all
   of the SQL-92 standard. Its a near perfect replacement for the old 
   shelve implementation.
    
"""

import os
import os.path
import sqlite

from current.db.currentdb import specificDB
from current.logger import *
from current.exception import CurrentSQLite
from current.db.pysqlite import schema

class PySqliteDB(specificDB):

    def __init__(self, config):
        """ Initialize the new database object. """

        self.config = config
        self.conn = None
        self.cursor = None

        # We steal a dir off the main current dir for our database.
        self.db_dir = os.path.join(self.config['current_dir'], 'db')

        self.db_file = os.path.join(self.db_dir, 'current.sqlite')

        # Make sure the directory exists
        if not os.access(self.db_dir, os.W_OK):
            if os.access(self.db_dir, os.F_OK):
                raise CurrentSQLite("No write access to DB file.")
            else:
                os.makedirs(self.db_dir)


    def __del__(self):
        self.disconnect()

        
    def disconnect(self):
        """ Close down the database file. """
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
                                                                        

    def initdb(self):
        """ Do the steps necessary to create an empty database.

        This should be enough to get the mod_python module working.
        """
        self.getConnection()
        self.getCursor()

        # initialize the database schema
        # FIXME: Naturally, we should require some extra 'force' variable
        # to overwrite the database here.
        self.cursor.execute(schema.INITDB)
        self.conn.commit()


    def getConnection(self):
        if self.conn == None:
            try:
                self.conn = sqlite.connect(db=self.db_file)
            except Exception, e:
                log("Exception raised in sqlite.connect()", MANDATORY)
                raise
            
        return self.conn


    def getCursor(self):
        if self.conn == None:
            self.getConnection()
            
        if self.cursor == None:
            self.cursor = self.conn.cursor()

        return self.cursor
     

## END OF LINE ##
