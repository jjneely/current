""" An implementation of currents backend as an sqlite database.

   Sqlite is a single file 'embedded' database that supports nearly all
   of the SQL-92 standard. Its a near perfect replacement for the old 
   shelve implementation.
    
"""

import os

from db.currentdb import CurrentDB

import sqlite
import schema


class PySqliteDB(CurrentDB):

    def __init__(self):
        """ Initialize the new database object. 

        We simply setup the internal dictionary here.
        """

        self.conn = None
        self.cursor = None


    def __del__(self):
        """ Close down the database file. """
        self.cursor.close()
        self.conn.close()


    def initdb(self, config):
        """ Do the steps necessary to create an empty database.

        This should be enough to get the mod_python module working.
        """
        # Remember, you cannot use the logger here...
    
        # call the parent FIRST
        CurrentDB.initdb(self, config)

        # We steal a dir off the main current dir for our database.
        db_dir = os.path.join(config['current_dir'], 'db')
        os.system('mkdir -p %s' % db_dir)

        db_file = os.path.join(db_dir, 'current.sqlite')
        self.conn = sqlite.connect(db=db_file, autocommit=1)
        self.cursor = self.conn.cursor()

        # initialize the database schema
        # FIXME: Naturally, we should require some extra 'force' variable
        # to overwrite the database here.
        self.cursor.execute("BEGIN;")
        self.cursor.execute(schema.INIT_DB)

        # Put the basic config items in the config table.
        sql = """ INSERT INTO config VALUES(%s, %s); """
        records = [['schema_rev', schema.VERSION]]
        for key in ['log_file', 'log_level', 'current_dir']:
            records.append([key, config[key]])

        self.cursor.executemany(sql, records)
        self.cursor.execute("COMMIT;")


    def addRpmDir(dirname):
        """ Add an entire directory of rpms all at once """
    
        if not os.path.isdir(dirname):
            print "Warning: %s was not a valid dir" % dirname
            return
    
        for file in os.listdir(dirname):
            pathname = os.path.join(dirname, file)
            addRpmPackage(pathname)


    def addRpmPackage(pathname):
        """ Add a single Rpm to the channel. 
    
        PLEASE NOTE that you must keep this method and _deleteRpmPackage in
        sync.
        """
        
        # Grab all the info we need out of the rpm itself.
        filename = os.path.basename(pathname)
        print "Examing %s" % filename
        rpm_info = getRpmInfo(pathname)
    
        cursor.execute("BEGIN TRANSACTION;")
    
        package_id = _insertPackageTable(rpm_info)
        rpm_id = _insertRpmTable(rpm_info, package_id)
    
        cursor.execute("COMMIT TRANSACTION");
    
    
    def _insertPackageTable(rpm_info):
        """ Insert data from rpm_info into the PACKAGE table """
    
        # try to grab the package_id of this rpm
        package_id = _getPackageId(rpm_info['name'], rpm_info['version'], 
                                   rpm_info['release'], rpm_info['epoch'])
    
        # If its not in the database at all, insert it...
        if not package_id:
            sql = """INSERT INTO packages VALUES(NULL, %s, %s, %s, %s);"""
            args = (rpm_info['name'], rpm_info['version'], 
                     rpm_info['release'], rpm_info['epoch'])
            print "Inserting", os.path.basename(rpm_info['pathname'])
            cursor.execute(sql, args)
    
        # And now we can get the package_id...
        package_id = _getPackageId(rpm_info['name'], rpm_info['version'], 
                                   rpm_info['release'], rpm_info['epoch'])
        assert package_id
                
        return package_id
    
    
    def _insertRpmTable(rpm_info, package_id):
        """ Insert data from rpm_info into the RPM table """
    
        # try to grab the rpm_id of this rpm
        rpm_id = _getRpmId(rpm_info['pathname'])
    
        # If its not in the database at all, insert it...
        if not rpm_id:
            sql = """INSERT INTO rpms VALUES(NULL, %s, %s, %s, %s, %s, %s);"""
            args = (package_id, rpm_info['pathname'], rpm_info['arch'], 
                    rpm_info['size'], 0, 0)
            cursor.execute(sql, args)
    
        # And now we can get the rpm_id...
        rpm_id = _getRpmId(rpm_info['pathname'])
        assert rpm_id
            
        return rpm_id


    def getPackageId(name, version, release, epoch):
        """ Get the package_id for a given packages data """
    
        # We might need less specific queries later...
        sql = """SELECT package_id FROM packages 
                     WHERE packages.name == %s     
                       AND packages.version == %s  
                       AND packages.release == %s  
                       AND packages.epoch   == %s;"""
    
        args = (name, version, release, epoch)
    
        cursor.execute(sql, args)
        # There SHOULD be only 1 or 0 rows - no other answer is valid
        # according to the database constraints
        assert cursor.rowcount == 1 or cursor.rowcount == 0
    
        # Grab the whole result at once
    #    print "_getPackageId() rowcount", cursor.rowcount   # log debug2
        row = cursor.fetchone()
    
        if cursor.rowcount == 0:
            return None
        else:
            return row[0]
    
    
    def getRpmId(pathname):
        """ Get the rpm_id for a given rpm pathname """
    
        sql = """SELECT rpm_id FROM rpms
                     WHERE rpms.pathname == %s;"""     
        args = (pathname)
    
        cursor.execute(sql, args)
        # There SHOULD be only 1 or 0 rows - no other answer is valid
        # according to the database constraints
        assert cursor.rowcount == 1 or cursor.rowcount == 0
    
        # Grab the whole result at once
    #    print "_getRpmId() rowcount", cursor.rowcount   # log debug2
        row = cursor.fetchone()
    
        if cursor.rowcount == 0:
            return None
        else:
            return row[0]
    

## END OF LINE ##
