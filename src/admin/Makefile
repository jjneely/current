# 
# Makefile for installing the database package for current
#

MODULES			= __init__ add_dir create_channel scan test
PYFILES         = $(addsuffix .py,  $(MODULES))
OBJECTS         = $(addsuffix .pyc, $(MODULES))

INSTALL_DIRS	= $(DATA_DIR)/admin

SUBDIRS 		=  


# default python rules:
%.pyc: %.py
	python -c "import py_compile; py_compile.compile('$<')"

all:: $(OBJECTS)

files: $(PYFILES)

install:: $(OBJECTS)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(DATA_DIR)/admin

	$(INSTALL_DATA) $(PYFILES) $(OBJECTS) $(INSTALL_ROOT)$(DATA_DIR)/admin

clean::
	@rm -fv *.pyc *.pyo *~

# Now do the same in the subdirs
all install clean:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done

