INITDB = """

CREATE TABLE CHANNEL (
  channel_id             int(11)       NOT NULL auto_increment,
  parentchannel_id       int(11) default NULL,
  name                   varchar(64) NOT NULL default '',
  label                  varchar(64) NOT NULL default '',
  arch                   varchar(64) NOT NULL default '',
  osrelease              varchar(64) NOT NULL default '',
  description            text,
  lastupdate             varchar(64) default NULL,

  PRIMARY KEY  (channel_id)
) TYPE=MyISAM;

CREATE TABLE CHANNEL_DIR (
  channel_dir_id         int(11)       NOT NULL auto_increment,
  channel_id             int(11)       NOT NULL default '0',
  dirpathname            text,
  is_bin_dir             tinyint(1)    NOT NULL default '0',

  PRIMARY KEY (channel_dir_id),
  KEY channel_dir_chan_id_idx (channel_id)
) TYPE=MyISAM;

CREATE TABLE PACKAGE (
  package_id             int(11)       NOT NULL auto_increment,
  pkgname                varchar(64)   NOT NULL default '',
  version                varchar(64)   NOT NULL default '',
  release                varchar(32)   NOT NULL default '',
  epoch                  varchar(8)    default NULL,

  PRIMARY KEY (package_id),
  KEY pkgname_idx (pkgname),
  KEY version_idx (version),
  KEY release_idx (release),
  KEY epoch_idx (epoch)
) TYPE=MyISAM;

CREATE TABLE RPM (
  rpm_id                 int(11)       NOT NULL auto_increment,
  package_id             int(11)       NOT NULL default '0',
  srpm_id                int(11)       default NULL,
  pathname               text          NOT NULL,
  arch                   varchar(32)   NOT NULL default '',
  size                   int(11)       NOT NULL default '0',
  original_channel_id    int(11)       NOT NULL default '0',
  active_channel_id      int(11)       default NULL,

  PRIMARY KEY  (rpm_id),
  KEY package_id_idx (package_id),
  KEY active_channel_id_idx (active_channel_id),
  KEY srpm_id_idx (srpm_id)
) TYPE=MyISAM;

CREATE TABLE RPMOBSOLETE (
  rpmobsolete_id         int(11)       NOT NULL auto_increment,
  rpm_id                 int(11)       NOT NULL default '0',
  name                   varchar(64)   default NULL,
  flags                  varchar(64)   default NULL,
  vers                   varchar(64)   default NULL,

  PRIMARY KEY  (rpmobsolete_id),
  KEY rpmosbolete_rpm_id_idx (rpm_id)
) TYPE=MyISAM;

CREATE TABLE RPMPROVIDE (
  rpmprovide_id          int(11)       NOT NULL auto_increment,
  rpm_id                 int(11)       NOT NULL default '0',
  name                   text,
  flags                  varchar(64)   default NULL,
  vers                   varchar(64)   default NULL,

  PRIMARY KEY  (rpmprovide_id),
  KEY rpmprovide_rpm_id_idx (rpm_id)
) TYPE=MyISAM;

CREATE TABLE SRPM (
  srpm_id                int(11)       NOT NULL auto_increment,
  filename               text          NOT NULL,
  pathname               text          NOT NULL,

  PRIMARY KEY  (srpm_id)
) TYPE=MyISAM;
"""
