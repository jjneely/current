# 
# Makefile for installing the docs for current
#

all: current-guide-html current-guide-ps

current-guide-html: guide-source
	db2html current-guide.sgml

current-guide-ps: guide-source
	db2ps current-guide.sgml

guide-source: client.sgml configuration.sgml current-guide.sgml installation.sgml maintaining.sgml

# There is no standard place to put html/ps documentation, so, I don't.
install:
	@echo Nothing to do here.

sedrules:
	@echo Nothing to do here.

clean:
	@rm -rfv ./current-guide/
	@rm -fv current-guide.ps *.log *.aux *.tex *~

# END OF LINE #
