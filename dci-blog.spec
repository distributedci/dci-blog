Name:        dci-blog
Version:     0.1.0
Release:     1.VERS%{?dist}
Summary:     The Official blog of Distributed-CI

License:     ASL2.0
URL:         https://github.com/redhat-cip/dci-blog
Source0:     dci-blog-%{version}.tar.gz

Requires:    httpd
BuildArch:   noarch

%description
The Official blog of Distributed-CI ready to be served by a web server.

%prep
%setup -c

%build
rm -rf venv
%{__python3} -m venv venv 1>&2
%{_builddir}/dci-blog-%{version}/venv/bin/python -m pip install -r requirements.txt 1>&2
%{_builddir}/dci-blog-%{version}/venv/bin/pelican ./content -o ./output -s ./pelicanconf.py 1>&2

%install
install -d %{buildroot}/var/www/html/blog
cp -r output/* %{buildroot}/var/www/html/blog

%files
/var/www/html/blog/*

%changelog
* Thu Feb 24 2022 Guillaume Vincent <gvincent@redhat.com> 0.1.0-1
- Initial commit
