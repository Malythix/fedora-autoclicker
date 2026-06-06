Name:           fedora-auto-clicker
Version:        1.0.0
Release:        1%{?dist}
Summary:        All-in-one automation tool with clicker, macros and key combos
License:        GPLv3
URL:            https://github.com/Malythix/fedora-autoclicker
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3, python3-libevdev, python3-tkinter

%description
Nobara Auto Clicker is a powerful automation utility for Linux.
It offers flexible auto-clicking with randomization, keyboard combinations,
macro recording/playback, scheduled starts, idle detection, and profile support.
All dependencies are bundled, no pip required.

%prep
%setup -q -n fedora-auto-clicker

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
# Projektinhalt kopieren (außer spec, Makefile etc.)
cp -r fedora-auto-clicker.py libs/ lang.json profiles/ fedora-auto-clicker.svg %{buildroot}%{_datadir}/%{name}/
# Symlink für den Befehl
ln -s ../share/%{name}/fedora-auto-clicker.py %{buildroot}%{_bindir}/fedora-auto-clicker
chmod +x %{buildroot}%{_datadir}/%{name}/fedora-auto-clicker.py

# Desktop-Datei und Icon installieren
mkdir -p %{buildroot}%{_datadir}/applications
cp fedora-auto-clicker.desktop %{buildroot}%{_datadir}/applications/
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp fedora-auto-clicker.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%{_bindir}/fedora-auto-clicker
%{_datadir}/%{name}/
%{_datadir}/applications/fedora-auto-clicker.desktop
%{_datadir}/icons/hicolor/scalable/apps/fedora-auto-clicker.svg

%post
update-desktop-database &>/dev/null || :
