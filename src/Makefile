# 
# Makefile for installing the python modules for current
#

MODULES			= archtab auth configure \
                  ConstructParser current_apache \
                  logger rpm_wrapper
PYFILES         = $(addsuffix .py,  $(MODULES))
OBJECTS         = $(addsuffix .pyc, $(MODULES))

INSTALL_DIRS	= $(DATA_DIR)

SUBDIRS = db api


# default python rules:
%.pyc: %.py
	python -c "import py_compile; py_compile.compile('$<')"

all:: sedrules $(OBJECTS)

files: $(PYFILES)

sedrules: configure.py 
	sed -e 's%^VERSION=.*%VERSION="$(VERSION)"%' \
        -e 's%^MODULES_DIR=.*%MODULES_DIR="$(DATA_DIR)"%' \
        -e 's%^CONFIG_DIR=.*%CONFIG_DIR="$(SYSCONF_DIR)"%' \
        -e 's%^LOG_DIR=.*%LOG_DIR="$(LOG_DIR)"%' \
        -e 's%^PID_DIR=.*%PID_DIR="$(PID_DIR)"%' \
        -e '1 s%#!.*%#! $(PYTHON_BIN)%' \
        < $< > $<.tmp
	mv -f $<.tmp $<  
	
install:: $(OBJECTS)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(DATA_DIR)

	$(INSTALL_DATA) $(PYFILES) $(OBJECTS) $(INSTALL_ROOT)$(DATA_DIR)

clean:: 
	@rm -fv *.pyc *.pyo *~

# Now do the same in the subdirs
all install clean:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done



