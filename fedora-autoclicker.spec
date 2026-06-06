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

%prep
%setup -q

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -r * %{buildroot}%{_datadir}/%{name}/
ln -s %{_datadir}/%{name}/fedora-auto-clicker.py %{buildroot}%{_bindir}/fedora-auto-clicker
chmod +x %{buildroot}%{_bindir}/fedora-auto-clicker

mkdir -p %{buildroot}%{_datadir}/applications
cp %{name}.desktop %{buildroot}%{_datadir}/applications/
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp %{name}.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%{_bindir}/fedora-auto-clicker
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg

%post
update-desktop-database &>/dev/null || :
