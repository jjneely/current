VERSION = 1

INIT_DB = """
-- This SQL script creates the sqlite schema for the Current database

-- Sqlite doesn't have explicit sequences, however,
--   columns declared integer primary keys automatically increment when 
--   you insert a NULL

-- Create the PACKAGES table
create table PACKAGES (
    package_id      integer primary key,
    name            varchar(64) not null,
    version         varchar(64) not null,
    release         varchar(64) not null,
    epoch           varchar(64) not null,
    arch            varchar(64) not null,
    unique (name, version, release, epoch, arch)
    );
create index PACKAGE_ID_IDX on PACKAGES(package_id);

-- Create the RPM filenames table
create table RPMS (
    rpm_id          integer primary key,
    package_id      int not null,
    pathname        varchar(1024) not null,
    size            varchar(64) not null,
    original_channel_id     int,
--    original_channel_id     int not null,
    active_channel_id       int
    );
create index RPM_ID_IDX on RPMS(rpm_id);
create index RPM_PACKAGE_ID_IDX on RPMS(package_id);
create index RPM_PATHNAME_IDX on RPMS(pathname);
create index RPM_ACTIVE_CHANNEL_ID_IDX on RPMS(active_channel_id);

--  Create the SRPMS table
create table SRPMS (
    srpm_id         integer primary key,
    rpm_id          int not null,
    filename        varchar(1024) not null
    );
create index SRPM_ID_IDX on SRPMS(srpm_id);
create index SRPM_RPM_ID_IDX on SRPMS(rpm_id);
create index SRPM_FILENAME_IDX on SRPMS(filename);

-- Create the table of provides information
create table PROVIDES (
    provide_id      integer primary key,
    package_id      int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index PROVIDE_ID_IDX on PROVIDES(provide_id);
create index PROVIDE_RPM_ID_IDX on PROVIDES(rpm_id);

-- Create the table of obsoletes information
create table OBSOLETES (
    obsolete_id     integer primary key,
    package_id      int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index OBSOLETE_ID_IDX on OBSOLETES(obsolete_id);
create index OBSOLETE_RPM_ID_IDX on OBSOLETES(rpm_id);
                    
-- Create the table of channels
create table CHANNELS (
    channel_id      integer primary key,
    parentchannel_id     int,
    label           varchar(64),
    name            varchar(64),
    arch            varchar(64),
    osrelease       varchar(64),
    description     varchar(1024),
    srpm_check      varchar(64),
    lastupdate      timestamp
    );
create index CHANNEL_ID_IDX on CHANNELS(channel_id);

-- Create the channel dir table
create table CHANNELDIRS (
    channel_id      int,
    dir             varchar(1024),
    srpm_flag       varchar(64)
    );
create index CHANNELDIR_ID_IDX on CHANNELDIRS(channel_id, srpm_flag);

-- Create the config table
-- The only config elements stored here are the ones needed 
--   once the database is opened. Anything required to get to the 
--   database or create the database are in current.conf.
--
-- Because of the file based nature of pysqlite, current_dir is stored
--   in BOTH.
create table CONFIG (
    key             varchar(64),
    value           varchar(1024)
    );
create index CONFIG_KEY_IDX on CONFIG(key);

-- Changelist from postgres schema
--
-- 1. packages.pkgname changed to packages.name
-- 2. packages.epoch made NOT NULL,
-- 3. Took "RPM" off the front of obsoletes and provides
-- 4. put arch back into PACKAGE
-- 5. added filename indexes
-- 6. added config table.

"""

