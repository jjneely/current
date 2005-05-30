# 
# Makefile for installing the database package for current
#

MODULES			= 
PYFILES         = $(addsuffix .py,  $(MODULES))
OBJECTS         = $(addsuffix .pyc, $(MODULES))
MISC            = summary.html channels.html channels.table.html \
				  template.html

INSTALL_DIRS	= $(DATA_DIR)/templates

SUBDIRS 		= htdocs 


# default python rules:
%.pyc: %.py
	python -c "import py_compile; py_compile.compile('$<')"

all:: $(OBJECTS)

files: $(PYFILES)

install:: $(OBJECTS) $(MISC)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(DATA_DIR)/templates

	$(INSTALL_DATA) $(PYFILES) $(OBJECTS) $(MISC) $(INSTALL_ROOT)$(DATA_DIR)/templates

clean::
	@rm -fv *.pyc *.pyo *~

sedrules::
	@echo "Nothing to do here."

# Now do the same in the subdirs
all install clean:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done

