INITDB = """
-- This SQL script creates the SQLite schema for the Current database

create table PACKAGE (
    package_id      INTEGER PRIMARY KEY,
    name            varchar(64) not null,
    version         varchar(64) not null,
    release         varchar(64) not null,
    epoch           varchar(8) not null,
    issource        smallint not null
    );
create index PACKAGE_NAME_IDX on PACKAGE(name);
create index PACKAGE_VERSION_IDX on PACKAGE(version);
create index PACKAGE_RELEASE_IDX on PACKAGE(release);
                    
create table RPM (
    rpm_id          INTEGER PRIMARY KEY,
    package_id      int not null,
    filename        varchar(1024) unique not null,
    arch            varchar(32) not null,
    size            varchar(32) not null
    );
create index RPM_PACKAGE_ID_IDX on RPM(package_id);
create index RPM_FILENAME_IDX on RPM(filename);

create table CHANNEL_RPM (
    channel_rpm_id  INTEGER PRIMARY KEY,
    rpm_id          int not null,
    channel_id      int not null
    );
create index CHANNEL_RPM_RPM_ID_IDX on CHANNEL_RPM(rpm_id);
create index CHANNEL_RPM_CHANNEL_ID_IDX on CHANNEL_RPM(channel_id);

create table CHANNEL_RPM_ACTIVE (
    active_id   INTEGER PRIMARY KEY,
    rpm_id      int not null,
    channel_id     int not null
    );
create index CHANNEL_RPM_ACTIVE_CHANNEL_ID_IDX on CHANNEL_RPM_ACTIVE(channel_id);

create table RPMPROVIDE (
    rpmprovide_id   INTEGER PRIMARY KEY,
    rpm_id          int not null,
    name            varchar(4096),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMPROVIDE_RPM_ID_IDX on RPMPROVIDE(rpm_id);

create table RPMPAYLOAD (
    rpmpayload_id   INTEGER PRIMARY KEY,
    rpm_id          int not null,
    name            varchar(4096)
    );

create table RPMOBSOLETE (
    rpmobsolete_id  INTEGER PRIMARY KEY,
    rpm_id          int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMOBSOLETE_RPM_ID_IDX on RPMOBSOLETE(rpm_id);
                    
create table CHANNEL (
    channel_id      INTEGER PRIMARY KEY,
    parentchannel_id     int,
    name            varchar(64) unique not null,
    label           varchar(64) unique not null,
    arch            varchar(64) not null,
    osrelease       varchar(64) not null,
    description     varchar(1024),
    lastupdate      varchar(64)
    );

create table CHANNEL_DIR (
    channel_dir_id  INTEGER PRIMARY KEY,
    channel_id      int not null,
    dirpathname     varchar(1024)
    );
create index CHANNEL_DIR_CHAN_ID_IDX on CHANNEL_DIR(channel_id);

"""
