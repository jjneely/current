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
    dep             text not null,
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
    lastupdate      varchar(64),
    base            int
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
   sid            varchar(40) unique not null,
   createtime     float not null,
   timeout        float not null,
   data           text
);
create index SESSION_IDX on SESSIONS(sid);

create table PROFILE (
    profile_id      INTEGER PRIMARY KEY,
    user_id	    int not null,
    architecture    varchar(64) not null,
    cannon_arch     varchar(32) not null,
    os_release      varchar(32) not null,
    name            varchar(128) not null,
    release_name    varchar(64),
    uuid            varchar(40) not null unique
);
create index PROFILE_IDX on PROFILE(uuid);

create table PROFILE_QUEUE (
    queue_id        INTEGER PRIMARY KEY,
    profile_id      int not null,
    begindate       datetime not null,
    enddate         datetime,
    status          int not null,
    method          varchar(32) not null,
    params          text not null,
    submit_code     integer,
    submit_msg      varchar(64),
    submit_data     text
);
create index PROFILE_QUEUE_IDX on PROFILE_QUEUE(profile_id);

create table SUBSCRIPTIONS (
    sub_id          INTEGER PRIMARY KEY,
    profile_id      int not null,
    channel_id      int not null
);
create index SUBSCRIPTIONS_PROFILE_IDX on SUBSCRIPTIONS(profile_id);

create table USER (
    user_id         INTEGER PRIMARY KEY,
    username        varchar(32) not null,
    password        varchar(40) not null,
    email           varchar(40) not null,
    company         varchar(32),
    position        varchar(32),
    title           varchar(32),
    first_name      varchar(32) ,
    last_name       varchar(32),
    address1        varchar(32),
    address2        varchar(32),
    city            varchar(32),
    zip             varchar(32),
    state           varchar(32),
    country         varchar(32),
    fax             varchar(32),
    phone           varchar(32),
    contact_email   boolean,
    contact_fax     boolean,
    contact_mail    boolean,
    contact_newsletter boolean,
    contact_phone   boolean
);

create table HARDWARE (
    hardware_id     INTEGER PRIMARY KEY,
    profile_id      int not null,
    class           varchar(32),
    dict            text
);
create index HARDWARE_PROFILE_IDX on HARDWARE(profile_id);

create table INSTALLED (
    installed_id    INTEGER PRIMARY KEY,
    profile_id      int not null,
    package_id      int not null,
    info            int not null
);
create index INSTALLED_PROFILE_IDX on INSTALLED(profile_id);

"""
