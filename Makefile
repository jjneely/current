#
# Makefile for current
#

# We export all the vars from the top level to sub-makes
export

# Things that change from build to build
PROJECT			= current
VERSION		 	= 1.5.0
PYTHON_BIN	 	= /usr/bin/python
PREFIX		 	= /usr
INSTALL_ROOT 	=

# File lists. (change rarely)
PROGRAMS		= cadmin cinstall
CONFIG			= current.conf
SRC				= src
DOC             = docs CHANGELOG LICENSE README TODO RELEASE-NOTES
MISC            = Makefile future support tar-excludes

ALLFILES        = $(PROGRAMS) $(SRC) $(CONFIG) $(DOC) $(MISC)

SUBDIRS			= src docs

# Autoconf calls it data, but we're sticking python portable modules there.
DATA_DIR		= $(PREFIX)/share/$(PROJECT)
SBIN_DIR        = $(PREFIX)/sbin
SYSCONF_DIR     = /etc/$(PROJECT)

LOG_DIR         = /var/log/httpd
PID_DIR         = /var/run

INSTALL_DIRS	= $(SBIN_DIR) $(SYSCONF_DIR) $(LOG_DIR) # $(PID_DIR)

# INSTALL scripts
INSTALL         = install --verbose 
INSTALL_BIN     = $(INSTALL) -m 755 
INSTALL_DIR     = $(INSTALL) -m 755 -d 
INSTALL_DATA    = $(INSTALL) -m 644 


all:: sedrules files

files: $(ALLFILES)

sedrules:: sedspec sedcadmin sedcinstall

sedspec: support/current.spec
	sed -e 's%Version:.*%Version: $(VERSION)%' < $< > $<.tmp
	mv -f $<.tmp $<

sedcadmin: cadmin
	sed -e 's%^VERSION=.*%VERSION="$(VERSION)"%' \
            -e 's%^MODULES_DIR=.*%MODULES_DIR="$(DATA_DIR)"%' \
            -e 's%^CONFIG_DIR=.*%CONFIG_DIR="$(CONFIG_DIR)"%' \
            -e 's%^LOG_DIR=.*%LOG_DIR="$(LOG_DIR)"%' \
            -e 's%^PID_DIR=.*%PID_DIR="$(PID_DIR)"%' \
            -e '1 s%#!.*%#! $(PYTHON_BIN)%' \
        < $< > $<.tmp
	mv -f $<.tmp $<
	chmod u+x $<

sedcinstall: cinstall
	sed -e 's%^VERSION=.*%VERSION="$(VERSION)"%' \
            -e 's%^MODULES_DIR=.*%MODULES_DIR="$(DATA_DIR)"%' \
            -e 's%^CONFIG_DIR=.*%CONFIG_DIR="$(CONFIG_DIR)"%' \
            -e 's%^LOG_DIR=.*%LOG_DIR="$(LOG_DIR)"%' \
            -e 's%^PID_DIR=.*%PID_DIR="$(PID_DIR)"%' \
            -e '1 s%#!.*%#! $(PYTHON_BIN)%' \
        < $< > $<.tmp
	mv -f $<.tmp $<
	chmod u+x $<

devel:
	@make sedrules DATA_DIR=$$PWD/src CONFIG_DIR=$$PWD

debug:: 
	@echo INSTALL_DIRS=$(INSTALL_DIRS)
	@echo ALLFILES=$(ALLFILES)

snapshot: 
	make release VERSION=0.`date +%Y%m%d`

release: sedrules
	rm -rf $(PROJECT)-$(VERSION).tar.gz $(PROJECT)-$(VERSION)
	mkdir $(PROJECT)-$(VERSION)
	cp -ra $(ALLFILES) $(PROJECT)-$(VERSION)
	tar czf $(PROJECT)-$(VERSION).tar.gz -X tar-excludes $(PROJECT)-$(VERSION)
	rm -rf $(PROJECT)-$(VERSION)

install:: sedrules
	$(INSTALL_DIR) $(INSTALL_ROOT)$(SBIN_DIR)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(SYSCONF_DIR)

	$(INSTALL_BIN) cadmin $(INSTALL_ROOT)$(SBIN_DIR)/cadmin
	$(INSTALL_DATA) $(CONFIG) $(INSTALL_ROOT)$(SYSCONF_DIR)

clean::
	@rm -fv *.pyc *.pyo *~ .*~ current.log

# Now do the same in the subdirs
all install clean sedrules:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done

# END OF LINE #
