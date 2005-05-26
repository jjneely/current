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

create table DEPENDANCIES (
    dep_id          INTEGER PRIMARY KEY,
    dep             varchar(4096) not null,
    rpm_id          int not null,
    type            int not null,
    flags           varchar(64),
    vers            varchar(64)
    );
create index DEPENDANCIES_RPM_IDX on DEPENDANCIES(rpm_id);
create index DEPENDANCIES_TYPE_IDX on DEPENDANCIES(type);
create index DEPENDANCIES_DEP_IDX on DEPENDANCIES(dep);

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
create index CHANNEL_LABEL_IDX on CHANNEL(label);

create table CHANNEL_DIR (
    channel_dir_id  INTEGER PRIMARY KEY,
    channel_id      int not null,
    dirpathname     varchar(1024)
    );
create index CHANNEL_DIR_CHAN_ID_IDX on CHANNEL_DIR(channel_id);

create table SESSIONS (
   session_id     INTEGER PRIMARY KEY,
   sid            varchar(32) unique not null,
   createtime     float not null,
   timeout        float not null,
   data           text
);
create index SESSION_IDX on SESSIONS(sid);

create table PROFILE (
    profile_id      INTEGER PRIMAEY KEY,
    architecture    varchar(64) not null,
    os_release      varchar(32) not null,
    name            varchar(128) not null,
    release_name    varchar(64),
    rhnuuid         varchar(32) not null,
    username        varchar(32),
    uuid            varchar(32)
);

create table HARDWARE (
    hardware_id     INTEGER PRIMARY KEY,
    profile_id      int not null,
    class           varchar(32),
    dict            text
);

create table INSTALLED (
    installed_id    INTEGER PRIMARY KEY,
    package_id      int not null,
    profile_id      int not null
);
create index INSTALLED_PACKAGE_IDX on INSTALLED(package_id);
create index INSTALLED_PROFILE_IDX on INSTALLED(profile_id);

"""
