# 
# Makefile for installing the database package for current
#

MODULES			= DummyLogger __init__ sgmlentitynames simpleElementTree \
				  simpleTALES simpleTAL simpleTALUtils
PYFILES         = $(addsuffix .py,  $(MODULES))
OBJECTS         = $(addsuffix .pyc, $(MODULES))

INSTALL_DIRS	= $(DATA_DIR)/simpletal

SUBDIRS 		=  


# default python rules:
%.pyc: %.py
	python -c "import py_compile; py_compile.compile('$<')"

all:: $(OBJECTS)

files: $(PYFILES)

install:: $(OBJECTS)
	$(INSTALL_DIR) $(INSTALL_ROOT)$(DATA_DIR)/simpletal

	$(INSTALL_DATA) $(PYFILES) $(OBJECTS) $(INSTALL_ROOT)$(DATA_DIR)/simpletal

clean::
	@rm -fv *.pyc *.pyo *~

# Now do the same in the subdirs
all install clean:: $(SUBDIRS)
	@for d in $(SUBDIRS) ; do $(MAKE) -C $$d $@ ; done

