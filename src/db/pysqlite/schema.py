
INIT_DB = """
-- This SQL script creates the sqlite schema for the Current database

-- Sqlite doesn't have explicit sequences, however,
--   columns declared integer primary keys automatically increment when 
--   you insert a NULL

-- Create the PACKAGES table
-- 'arch' should be put into a separate table for linking.
-- # I potentially agree, and it should go in the RPM table. 
create table PACKAGES (
    package_id      integer primary key,
    name            varchar(64) not null,
    version         varchar(64) not null,
    release         varchar(64) not null,
    epoch           varchar(64) not null,
    unique (name, version, release, epoch)
    );
create index PACKAGE_ID_IDX on PACKAGES(package_id);
                    
-- Create the RPM filenames table
create table RPMS (
    rpm_id          integer primary key,
    package_id      int not null,
    pathname        varchar(1024) not null,
    arch            varchar(64) not null,
    size            varchar(64) not null,
    original_channel_id     int,
--    original_channel_id     int not null,
    active_channel_id       int
    );
create index RPM_ID_IDX on RPMS(rpm_id);
create index RPM_PACKAGE_ID_IDX on RPMS(package_id);
create index RPM_ACTIVE_CHANNEL_ID_IDX on RPMS(active_channel_id);

--  Create the SRPMS table
create table SRPMS (
    srpm_id         integer primary key,
    rpm_id          int not null,
    filename        varchar(1024) not null
    );
create index SRPM_ID_IDX on SRPMS(srpm_id);
create index SRPM_RPM_ID_IDX on SRPMS(rpm_id);

-- Create the table of provides information
create table RPMPROVIDES (
    rpmprovide_id   integer primary key,
    rpm_id          int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMPROVIDE_ID_IDX on RPMPROVIDES(rpmprovide_id);
create index RPMPROVIDE_RPM_ID_IDX on RPMPROVIDES(rpm_id);

-- Create the table of obsoletes information
create table RPMOBSOLETES (
    rpmobsolete_id  integer primary key,
    rpm_id          int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMOBSOLETE_ID_IDX on RPMOBSOLETES(rpmobsolete_id);
create index RPMOBSOLETE_RPM_ID_IDX on RPMOBSOLETES(rpm_id);
                    
-- Create the table of channels
create table CHANNELS (
    channel_id      integer primary key,
    parentchannel_id     int,
    name            varchar(64),
    arch            varchar(64),
    osrelease       varchar(64),
    description     varchar(1024),
    lastupdate      timestamp
    );
create index CHANNEL_ID_IDX on CHANNELS(channel_id);

"""

# Changelist from postgres schema
#
# 1. packages.pkgname changed to packages.name
# 2. packages.epoch made NOT NULL,
