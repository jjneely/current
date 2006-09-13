VERSION=1.7.5
NAME=current
TAG = $(VERSION)
REPO = http://current.tigris.org/svn/current

all:
	@echo "Nothing to build"

release: archive

archive:
	#svn cp $(REPO)/trunk $(REPO)/tags/$(TAG) -m "Tag $(TAG)"
	@rm -rf /tmp/$(NAME)-$(VERSION)
	@cd /tmp; svn export $(REPO)/trunk $(NAME)-$(VERSION) || :
	@cd /tmp/$(NAME)-$(VERSION); sed "s/VERSIONSUBST/$(VERSION)/" < support/$(NAME).spec.in > support/$(NAME).spec
	@cd /tmp/$(NAME)-$(VERSION); sed "s/VERSIONSUBST/$(VERSION)/" < setup.py.in > setup.py
	@dir=$$PWD; cd /tmp; tar -cvzf $$dir/$(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	@rm -rf /tmp/$(NAME)-$(VERSION)
	@echo "The archive is in $(NAME)-$(VERSION).tar.bz2"

