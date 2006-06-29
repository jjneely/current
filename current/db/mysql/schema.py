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
    lastupdate      varchar(64)
    ) Type=InnoDB auto_increment=1;


drop table if exists CHANNEL_DIR;
create table CHANNEL_DIR (
    channel_dir_id  INTEGER PRIMARY KEY auto_increment,
    channel_id      int not null,
    dirpathname     text,
    index(channel_id)
    ) Type=InnoDB;
"""
