INITDB = """
-- This SQL script creates the PostgreSQL schema for the Current database

create sequence package_id_seq;
create table PACKAGE (
    package_id      int default nextval('package_id_seq') unique not null,
    pkgname         varchar(64) not null,
    version         varchar(64) not null,
    release         varchar(32) not null,
    epoch           varchar(8)
    );
create index PACKAGE_ID_IDX on PACKAGE(package_id);
create index PACKAGE_NAME_IDX on PACKAGE(pkgname);
create index PACKAGE_VERSION_IDX on PACKAGE(version);
create index PACKAGE_RELEASE_IDX on PACKAGE(release);
                    
create sequence rpm_id_seq;
create table RPM (
    rpm_id          int default nextval('rpm_id_seq') unique not null,
    package_id      int not null,
    srpm_id         int,
    pathname        varchar(1024) not null,
    arch            varchar(32) not null,
    size            varchar(32) not null
    );
create index RPM_ID_IDX on RPM(rpm_id);
create index RPM_PACKAGE_ID_IDX on RPM(package_id);
create index RPM_SRPM_ID_IDX on RPM(srpm_id);

create sequence chan_rpm_orig_seq;
create table CHAN_RPM_ORIG (
    orig_id     int default nextval('chan_rpm_orig_seq') unique not null,
    rpm_id      int not null,
    chan_id     int not null
    );
create index OCHAN_RPM_ID_IDX on CHAN_RPM_ORIG(rpm_id);
create index OCHAN_CHAN_ID_IDX on CHAN_RPM_ORIG(chan_id);

create sequence chan_rpm_act_seq;
create table CHAN_RPM_ACT (
    act_id     int default nextval('chan_rpm_act_seq') unique not null,
    rpm_id      int not null,
    chan_id     int not null
    );
create index ACHAN_RPM_ID_IDX on CHAN_RPM_ACT(rpm_id);
create index ACHAN_CHAN_ID_IDX on CHAN_RPM_ACT(chan_id);

create sequence srpm_id_seq;
create table SRPM (
    srpm_id         int default nextval('srpm_id_seq') unique not null,
    filename        varchar(1024) not null,
    pathname        varchar(1024) not null
    );
create index SRPM_ID_IDX on SRPM(srpm_id);

create sequence rpmprovide_id_seq;
create table RPMPROVIDE (
    rpmprovide_id   int default nextval('rpmprovide_id_seq') unique not null,
    rpm_id          int not null,
    name            varchar(4096),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMPROVIDE_ID_IDX on RPMPROVIDE(rpmprovide_id);
create index RPMPROVIDE_RPM_ID_IDX on RPMPROVIDE(rpm_id);

create sequence rpmpayload_seq;
create table RPMPAYLOAD (
    rpmpayload_id   int default nextval('rpmpayload_seq') unique not null,
    rpm_id          int not null,
    name            varchar(4096)
    );
create index RPMPAYLOAD_RPM_ID_IDX on RPMPAYLOAD(rpm_id);

create sequence rpmobsolete_id_seq;
create table RPMOBSOLETE (
    rpmobsolete_id  int default nextval('rpmobsolete_id_seq') unique not null,
    rpm_id          int not null,
    name            varchar(64),
    flags           varchar(64),
    vers            varchar(64)
    );
create index RPMOBSOLETE_ID_IDX on RPMOBSOLETE(rpmobsolete_id);
create index RPMOBSOLETE_RPM_ID_IDX on RPMOBSOLETE(rpm_id);
                    
create sequence channel_id_seq;
create table CHANNEL (
    channel_id      int default nextval('channel_id_seq') unique not null,
    parentchannel_id     int,
    name            varchar(64) not null,
    label           varchar(64) not null,
    arch            varchar(64) not null,
    osrelease       varchar(64) not null,
    description     varchar(1024),
    lastupdate      varchar(64)
    );
create index CHANNEL_ID_IDX on CHANNEL(channel_id);

create sequence channel_dir_id_seq;
create table CHANNEL_DIR (
    channel_dir_id  int default nextval('channel_dir_id_seq') unique not null,
    channel_id      int not null,
    dirpathname     varchar(256)
    );
create index CHANNEL_DIR_ID_IDX on CHANNEL_DIR(channel_dir_id);
create index CHANNEL_DIR_CHAN_ID_IDX on CHANNEL_DIR(channel_id);

"""
