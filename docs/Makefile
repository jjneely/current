# 
# Makefile for installing the docs for current
#

all: current-guide-html 

current-guide-html: guide-source
	xmlto html -o current-guide  current-guide.xml

current-guide-ps: guide-source
	xmlto ps current-guide.xml
	#/bin/true

guide-source: client.xml configuration.xml current-guide.xml installation.xml maintaining.xml databases.xml

# There is no standard place to put html/ps documentation, so, I don't.
install:
	@echo Nothing to do here.

sedrules:
	@echo Nothing to do here.

clean:
	@rm -rfv ./current-guide/
	@rm -fv current-guide.ps *.log *.aux *.tex *~

# END OF LINE #
