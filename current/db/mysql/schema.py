INITDB =  """
drop table if exists PACKAGE;
create table PACKAGE (
    package_id      INTEGER PRIMARY KEY auto_increment,
    name            varchar(64) not null,
    version         varchar(64) not null,
    release         varchar(64) not null,
    epoch           varchar(8) not null,
    issource        smallint not null,
 
    index(name),
    index(version),
    index(release)
    ) Type=InnoDB;


drop table if exists RPM;
create table RPM (
    rpm_id          INTEGER PRIMARY KEY auto_increment,
    package_id      int not null,
    filename        text not null,
    arch            varchar(32) not null,
    size            varchar(32) not null,

    index(package_id)/*,
    index(filename)*/
    ) Type=InnoDB;


drop table if exists CHANNEL_RPM;
create table CHANNEL_RPM (
    channel_rpm_id  INTEGER PRIMARY KEY auto_increment,
    rpm_id          int not null,
    channel_id      int not null,

    index(rpm_id),
    index(channel_id)
    ) Type=InnoDB;


drop table if exists CHANNEL_RPM_ACTIVE;
create table CHANNEL_RPM_ACTIVE (
    active_id   INTEGER PRIMARY KEY auto_increment,
    rpm_id      int not null,
    channel_id     int not null,

    index(channel_id)
    ) Type=InnoDB;


drop table if exists DEPENDANCIES;
create table DEPENDANCIES (
    dep_id          INTEGER PRIMARY KEY auto_increment,
    dep             text,
    rpm_id          int not null,
    type            int not null,
    flags           varchar(64),
    vers            varchar(64),

    index(rpm_id),
    index(type)/*,
    index(dep)*/
    ) Type=InnoDB;


drop table if exists CHANNEL;
create table CHANNEL (
    channel_id      INTEGER PRIMARY KEY auto_increment,
    parentchannel_id     int,
    name            varchar(64) unique not null,
    label           varchar(64) unique not null,
    arch            varchar(64) not null,
    osrelease       varchar(64) not null,
    description     text,
    lastupdate      varchar(64),
    base            int,

    index(label)
    ) Type=InnoDB auto_increment=1;


drop table if exists CHANNEL_DIR;
create table CHANNEL_DIR (
    channel_dir_id  INTEGER PRIMARY KEY auto_increment,
    channel_id      int not null,
    dirpathname     text,

    index(channel_id)
    ) Type=InnoDB;

drop table if exists SESSIONS;
create table SESSIONS (
   session_id     INTEGER PRIMARY KEY auto_increment,
   sid            varchar(32) unique not null,
   createtime     float not null,
   timeout        float not null,
   data           text,

   index(sid)
) Type=InnoDB;

drop table if exists PROFILE;
create table PROFILE (
    profile_id      INTEGER PRIMARY KEY auto_increment,
    user_id         int not null,
    architecture    varchar(64) not null,
    cannon_arch     varchar(32) not null,
    os_release      varchar(32) not null,
    name            varchar(128) not null,
    release_name    varchar(64),
    uuid            varchar(40) not null unique,

    index(uuid)
) Type=InnoDB;

drop table if exists SUBSCRIPTIONS;
create table SUBSCRIPTIONS (
    sub_id          INTEGER PRIMARY KEY auto_increment,
    profile_id      int not null,
    channel_id      int not null
) Type=InnoDB;

drop table if exists USER;
create table USER (
    user_id         INTEGER PRIMARY KEY auto_increment,
    username        varchar(32) not null,
    password        varchar(40) not null,
    email           varchar(40) not null,
    company         varchar(32),
    position        varchar(32),
    title           varchar(32),
    first_name      varchar(32),
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
) Type=InnoDB;

drop table if exists HARDWARE;
create table HARDWARE (
    hardware_id     INTEGER PRIMARY KEY auto_increment,
    profile_id      int not null,
    class           varchar(32),
    dict            text
) Type=InnoDB;

drop table if exists INSTALLED;
create table INSTALLED (
    installed_id    INTEGER PRIMARY KEY auto_increment,
    profile_id      int not null,
    package_id      int not null,
    info            int(1) not null default '0',

    index(package_id),
    index(profile_id)
) Type=InnoDB;
"""
