##
# This package can no longer easily be built for RHL 7x, due to needing a 
# python 2.2 built with rpm support.
# 

Summary: A server for Red Hat's up2date tools.
Name: current
Version: 1.5.8
Release: 1
License: GPL
Group: System Environment/Daemons
URL: http://current.tigris.org
Source0: ftp://ftp.biology.duke.edu/pub/admin/current/%{name}-%{version}.tar.gz
Requires: python rpm-python mod_python mod_ssl 
Requires: rpm >= 4.0.2-8
Requires: httpd postgresql-server postgresql-python
BuildRequires: docbook-style-xsl docbook-style-dsssl docbook-dtds
BuildRequires: docbook-utils docbook-utils-pdf
BuildArchitectures: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot


%description
Current is a server implementation for Red Hat's up2date tools. It's
designed for small to medium departments to be able to set up and run their
own up2date server, feeding new applications and security patches to
workstations/servers.


%prep 
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
%setup -q


%build
make all


%install
make install INSTALL_ROOT=$RPM_BUILD_ROOT


%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc CHANGELOG LICENSE README RELEASE-NOTES TODO
%doc docs/*.txt docs/FAQ
%doc docs/client
%doc docs/developer_docs
%doc docs/current-guide.ps docs/current-guide
%config(noreplace) /etc/current/current.conf
%dir /etc/current
%dir /usr/share/current
/usr/sbin/*
/usr/share/current/*


%changelog
* Mon Sep 27 2004 Jack Neely <jjneely@gmail.com>
- Much cleanup of code.  The database code is very muched changed for
  the better and moved to the currentdb module.
- Beginings of error handling with exceptions

* Sat Nov 15 2003 Hunter Matthews <thm@duke.edu>
- Took out build support for RHL 7.x

* Thu Apr  3 2003 Hunter Matthews <thm@duke.edu>
- Fix Issuezilla #13, wrong URL in spec file.

* Mon Feb 17 2003 John Berninger <johnw@berningeronline.net> 1.5.3pre1
- Merged changes from postgres-branch into trunk, merged selected changes from
  1.4.x branch to trunk (7.x vs 8.x builds)

* Sat Feb 15 2003 Hunter Matthews <thm@duke.edu> 1.4.3-1
- Changes to dependancies to correct for Red Hat 8.0 

* Thu Oct 17 2002 Hunter Matthews <thm@duke.edu>
- Took out old code bits

* Sun Aug 18 2002 Hunter Matthews <thm@duke.edu>
- Took out current (old standalone server)
- Took out init.d for stunnel and current
- Removed stunnel requirement
- Added mod_python / mod_ssl requirement.

* Thu Mar 14 2002 Hunter Matthews <thm@duke.edu>
- Added more python library dependancies

* Sat Feb 23 2002 Hunter Matthews <thm@duke.edu>
- Took all the client stuff back out of current - we now have the site
  admin just build a new up2date.

* Mon Feb  4 2002 John Berninger <john_berninger@ncsu.edu>
- fixed spec file to put the cron file in the cron.d directory as opposed to
   cron.daily - stupid mistake on my part

* Thu Jan  3 2002 John Berninger <john_berninger@ncsu.edu>
- added a current-client package to the specfile along with a cron script

* Tue Dec 25 2001 Hunter Matthews <thm@duke.edu>
- Added init script and turned on pre and post install scripts

* Mon Dec 10 2001 Hunter Matthews <thm@duke.edu>
- Some cleanups and checked into the tree.
  Made the overall spec file layout match duke's template.

* Sun Dec 09 2001 Ivan F. Martinez <ivanfm@ecodigit.com.br>
- Initial release

# END OF LINE #
