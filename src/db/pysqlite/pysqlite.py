#! /usr/bin/python2

""" Channels store all the information for some collection of related rpms.

    Channels perform all the low-level DB/filesystem magic required 
    to organize, query, and otherwise deal with the RPM's themselves.
    
"""

import os
import os.path
import pprint
import rpm
import stat
import sys
import types
import sqlite

import sqlite_schema

SRC_DIRS = [
    '/local/linux/redhat-7.3/SRPMS',
    '/local/linux/updates/redhat-7.3/SRPMS',
]

RPM_DIRS = [
#     '/local/linux/redhat-7.3/RPMS',
#     '/local/linux/updates/redhat-7.3/RPMS/athlon',
#     '/local/linux/updates/redhat-7.3/RPMS/i386',
#     '/local/linux/updates/redhat-7.3/RPMS/i486',
#     '/local/linux/updates/redhat-7.3/RPMS/i586',
     '/local/linux/updates/redhat-7.3/RPMS/i686',
     '/local/linux/updates/redhat-7.3/RPMS/i686',
#    '/local/linux/updates/redhat-7.3/RPMS/noarch',
]

db = None
cursor = None

def _main():
    global db
    global cursor 

    # Open up the database 
    # I like this.... simple :)
    # 
    # We turn autocommit ?off? eh? anyway... we turn it off because 
    # current really does want to be able to rollback bad commits.
    db = sqlite.connect(db="db", autocommit=1)
    cursor = db.cursor()

    initdb()

    # add binaries
    for dir in RPM_DIRS:
        addRpmDir(dir)

    db.close()


def initdb():
    """ Initialize the database (tables, indexes, etc) """

    # initialize the database
    cursor.execute("BEGIN;")
    cursor.execute(sqlite_schema.INIT_DB)
    cursor.execute("COMMIT;")


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
        query = """INSERT INTO packages VALUES(NULL, %s, %s, %s, %s);"""
        args = (rpm_info['name'], rpm_info['version'], 
                 rpm_info['release'], rpm_info['epoch'])
        print "Inserting", os.path.basename(rpm_info['pathname'])
        cursor.execute(query, args)

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
        query = """INSERT INTO rpms VALUES(NULL, %s, %s, %s, %s, %s, %s);"""
        args = (package_id, rpm_info['pathname'], rpm_info['arch'], 
                rpm_info['size'], 0, 0)
        cursor.execute(query, args)

    # And now we can get the rpm_id...
    rpm_id = _getRpmId(rpm_info['pathname'])
    assert rpm_id
            
    return rpm_id


def getPackageId(name, version, release, epoch):
    """ Get the package_id for a given packages data """

    # We might need less specific queries later...
    query = """SELECT package_id FROM packages 
                 WHERE packages.name == %s     
                   AND packages.version == %s  
                   AND packages.release == %s  
                   AND packages.epoch   == %s;"""

    args = (name, version, release, epoch)

    cursor.execute(query, args)
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

    query = """SELECT rpm_id FROM rpms
                 WHERE rpms.pathname == %s;"""     
    args = (pathname)

    cursor.execute(query, args)
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


if __name__ == '__main__':
    _main()
    

## END OF LINE ##
