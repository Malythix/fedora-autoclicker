PREFIX ?= /usr

install:
	install -d $(DESTDIR)$(PREFIX)/share/fedora-auto-clicker
	cp -r * $(DESTDIR)$(PREFIX)/share/fedora-auto-clicker/
	ln -sf $(PREFIX)/share/fedora-auto-clicker/fedora-autoclicker.py $(DESTDIR)$(PREFIX)/bin/fedora-auto-clicker
	chmod +x $(DESTDIR)$(PREFIX)/bin/fedora-auto-clicker
	install -Dm644 fedora-auto-clicker.desktop $(DESTDIR)$(PREFIX)/share/applications/
	install -Dm644 fedora-auto-clicker.svg $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
