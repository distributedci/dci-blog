Name:        dci-doc
Version:     0.1.0
Release:     1.VERS%{?dist}
Summary:     The Official blog of Distributed-CI

License:     ASL2.0
URL:         https://github.com/redhat-cip/dci-doc
Source0:     dci-doc-%{version}.tar.gz

Requires:    httpd
BuildArch:   noarch

%description
The Official blog of Distributed-CI ready to be served by a web server.

%prep
%setup -q

%build
rm -rf venv
%{__python3} -m venv venv
%{_builddir}/dci-doc-%{version}/venv/bin/python -m pip install -r requirements.txt
%{_builddir}/dci-doc-%{version}/venv/bin/pelican ./content -o ./output -s ./pelicanconf.py

%install
install -d %{buildroot}/var/www/html/blog
cp -r output/* %{buildroot}/var/www/html/blog

%files
/var/www/html/blog/*

%changelog
* Thu Feb 24 2022 Guillaume Vincent <gvincent@redhat.com> 0.1.0-1
- Initial commit
