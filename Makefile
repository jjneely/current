VERSION=1.7.3
NAME=current
TAG = $(VERSION)
REPO = http://current.tigris.org/svn/current/trunk

all:
	@echo "Nothing to build"

release: archive

archive:
	#svn cp $(REPO)/trunk/$(NAME) $(REPO)/tags/$(NAME)/$(TAG) -m "Tag $(TAG)"
	@rm -rf /tmp/$(NAME)-$(VERSION)
	@cd /tmp; svn export $(REPO)/tags/$(NAME)/$(TAG) $(NAME)-$(VERSION) || :
	@cd /tmp/$(NAME)-$(VERSION)
	@sed "s/VERSIONSUBST/$(VERSION)/" < support/$(NAME).spec.in > support/$(NAME).spec
	@sed "s/VERSIONSUBST/$(VERSION)/" < setup.py.in > setup.py
	@dir=$$PWD; cd /tmp; tar -cvzf $$dir/$(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	@rm -rf /tmp/$(NAME)-$(VERSION)
	@echo "The archive is in $(NAME)-$(VERSION).tar.bz2"

