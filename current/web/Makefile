# 
# Makefile for installing the database package for current
#

MODULES			= channels __init__ summary
PYFILES         = $(addsuffix .py,  $(MODULES))
OBJECTS         = $(addsuffix .pyc, $(MODULES))
MISC            = 

INSTALL_DIRS	= $(DATA_DIR)/web

SUBDIRS 		= 


# default python rules:
%.pyc: %.py
	python -c "import py_compile; py_compile.compile('$<')"

all:: $(OBJECTS)

files: $(PYFILES)

install:: $(OBJECTS) $(MISC)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(DATA_DIR)/web

	$(INSTALL_DATA) $(PYFILES) $(OBJECTS) $(MISC) $(INSTALL_ROOT)$(DATA_DIR)/web

clean::
	@rm -fv *.pyc *.pyo *~

# Now do the same in the subdirs
all install clean:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done

