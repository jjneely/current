INITDB = """
-- This SQL script creates the PostgreSQL schema for the Current database

-- # Hunters changes
-- ! John's changes / comments

-- #
-- # I move the pkgname field to the (old RPM) Package table 
-- #
-- # I renamed RPM to PACKAGE
-- # I renamed RPMFILENAME to RPM
-- #
-- # Why?
-- #
-- # A. I've never been comfortable about that single field table
-- # B. we never get asked for 'kernel' - we always get asked for 
-- #    'kernel-2.2.2-18'
-- #
-- # C. With this structure, out "meta-data" is in the PACKAGE table,
-- #    and our concrete, bits-on-disk data is in the RPM table.
-- #
-- # I'd like to make _just_ the table names UPPER case, but to keep my
-- # diff size down, I left them for now. 
-- #
-- # Comments? Discussion?
-- #


-- Create the PACKAGES table
-- 'arch' should be put into a separate table for linking.
-- # I potentially agree, and it should go in the RPM table. 
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
                    
-- Create the RPM filenames table
create sequence rpm_id_seq;
create table RPM (
    rpm_id          int default nextval('rpm_id_seq') unique not null,
    package_id      int not null,
    srpm_id         int,
    pathname        varchar(1024) not null,
    arch            varchar(32) not null,
    size            int not null,
    original_channel_id     int not null,
    active_channel_id       int
    );
create index RPM_ID_IDX on RPM(rpm_id);
create index RPM_PACKAGE_ID_IDX on RPM(package_id);
create index RPM_ACTIVE_CHANNEL_ID_IDX on RPM(active_channel_id);
create index RPM_SRPM_ID_IDX on RPM(srpm_id);

--  Create the SRPMS table
-- ! This is a problem...  one SRPM can have multiple RPMS...  Need to remove
-- ! rpm_id from SRPM and insert srpm_id into RPM.
-- ! and done.
create sequence srpm_id_seq;
create table SRPM (
    srpm_id         int default nextval('srpm_id_seq') unique not null,
    filename        varchar(1024) not null,
    pathname        varchar(1024) not null
    );
create index SRPM_ID_IDX on SRPM(srpm_id);

-- Create the table of provides information
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

-- Create the table of obsoletes information
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
                    
-- Create the table of channels
-- ! Need to add label for API compatibility.  *sigh*
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

-- ! The following additional table is necessitated by removing channel
-- ! information from the current.conf file.
create sequence channel_dir_id_seq;
create table CHANNEL_DIR (
    channel_dir_id  int default nextval('channel_dir_id_seq') unique not null,
    channel_id      int not null,
    dirpathname     varchar(256),
    is_bin_dir      boolean not null
    );
create index CHANNEL_DIR_ID_IDX on CHANNEL_DIR(channel_dir_id);
create index CHANNEL_DIR_CHAN_ID_IDX on CHANNEL_DIR(channel_id);

"""
