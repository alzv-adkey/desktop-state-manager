Name:           desktop-state-manager
Version:        3.5
Release:        1%{?dist}
Summary:        Desktop state management tool with auto-restore and enhanced window placement

License:        GPL-3.0
URL:            https://github.com/desktop-state-manager
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

# Build dependencies
BuildRequires:  python3-devel
BuildRequires:  desktop-file-utils

# Runtime dependencies
Requires:       python3 >= 3.6
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       wmctrl
Requires:       jq
Requires:       bash

# Optional but recommended
Recommends:     gnome-shell-extension-tilingshell
Recommends:     zenity

%description
Desktop State Manager is a comprehensive tool for saving and restoring
desktop layouts, window positions, and application states. It features
a modern GTK4 interface with large, visible buttons and full CLI support.

Special support is included for TilingShell GNOME extension and other
tiling window managers.

Features:
- Save and restore desktop states
- Modern GTK4/Adwaita GUI interface  
- Command-line interface for automation
- TilingShell integration
- Auto-restore on login option
- Workspace and window position management

%prep
%setup -q

%build
# No compilation needed for this Python/shell application

%install
# Create directories
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_datadir}/applications

# Install main executables
install -m 755 desktop-state-manager %{buildroot}%{_bindir}/
install -m 755 desktop-state-manager-cli %{buildroot}%{_bindir}/

# Install application files
install -m 755 desktop-state-manager-simple.py %{buildroot}%{_datadir}/%{name}/
install -m 755 tilingshell-desktop-restore.sh %{buildroot}%{_datadir}/%{name}/
install -m 755 desktop-cli.sh %{buildroot}%{_datadir}/%{name}/
install -m 644 README.md %{buildroot}%{_datadir}/%{name}/

# Install desktop file
install -m 644 desktop-state-manager.desktop %{buildroot}%{_datadir}/applications/

# Install custom icons
install -d %{buildroot}%{_datadir}/icons/hicolor/16x16/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/24x24/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/32x32/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/48x48/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/64x64/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/128x128/apps
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

install -m 644 desktop-state-manager-16.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/desktop-state-manager.png
install -m 644 desktop-state-manager-24.png %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/desktop-state-manager.png
install -m 644 desktop-state-manager-32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/desktop-state-manager.png
install -m 644 desktop-state-manager-48.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/desktop-state-manager.png
install -m 644 desktop-state-manager-64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/desktop-state-manager.png
install -m 644 desktop-state-manager-128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/desktop-state-manager.png
install -m 644 desktop-state-manager.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/desktop-state-manager.svg

%check
# Validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/desktop-state-manager.desktop

%files
%doc README.md
%{_bindir}/desktop-state-manager
%{_bindir}/desktop-state-manager-cli
%{_datadir}/%{name}/
%{_datadir}/applications/desktop-state-manager.desktop
%{_datadir}/icons/hicolor/16x16/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/24x24/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/32x32/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/48x48/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/64x64/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/128x128/apps/desktop-state-manager.png
%{_datadir}/icons/hicolor/scalable/apps/desktop-state-manager.svg

%post
# Update desktop database
if [ $1 -eq 1 ] ; then
    /usr/bin/update-desktop-database &> /dev/null || :
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi

%postun
# Update desktop database
if [ $1 -eq 0 ] ; then
    /usr/bin/update-desktop-database &> /dev/null || :
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi

%changelog
* Sun Sep 01 2025 Desktop State Manager Team <dev@desktop-state-manager.org> - 3.5-1
- MAJOR RELEASE: Complete project modernization and infrastructure overhaul
- NEW: Comprehensive logging system with colored output, file rotation, and performance tracking
- NEW: Advanced configuration management with user-customizable settings and validation
- NEW: Professional backup system with compression, rotation, and metadata tracking
- NEW: Automated test suite with 16 tests covering all components (100% success rate)
- NEW: GitHub Actions CI/CD pipeline for automated testing and building
- NEW: Git repository with proper version control and contributing guidelines
- Enhanced error handling and recovery mechanisms throughout the codebase
- Performance optimizations and monitoring capabilities
- Professional documentation and development workflow
- Enterprise-ready infrastructure for sustainable development

* Thu Jun 26 2025 Desktop State Manager Team <dev@desktop-state-manager.org> - 3.4-1
- CRITICAL FIX: TilingShell tiling restored correctly for side-by-side apps (Outlook, Asana)
- Improved timing and delay handling between TilingShell restoration and manual adjustments
- Enhanced manual positioning logic for better alignment
- Reliable Telegram window detection and desktop assignment
- CRITICAL FIX: Virtual desktop restoration now works correctly
- Enhanced window matching algorithm with confidence scoring
- Windows now properly restore to their original virtual desktops
- Improved window identification using window IDs instead of fragile title matching
- Added enhanced timing and stabilization for window operations
- Better fallback strategies for window positioning
- Fixed issue where all apps restored to single virtual desktop
- More reliable window class and title matching

* Thu Jun 26 2025 Desktop State Manager Team <dev@desktop-state-manager.org> - 3.2-1
- MAJOR FIX: Enhanced application detection and restoration
- Fixed Chrome helper process duplication (no more extra windows)
- Improved Telegram detection as Flatpak application
- Enhanced Slack detection for /app/extra/ processes
- Added comprehensive helper process filtering
- Fixed desktop assignment restoration (apps now restore to correct virtual desktops)
- Better Flatpak app ID extraction from environment variables
- Improved bwrap process detection and handling
- All applications (Chrome, Slack, Telegram, Outlook) now restore correctly

* Tue Jun 17 2025 Desktop State Manager Team <dev@desktop-state-manager.org> - 2.0-1
- Major rewrite with working GUI interface
- Added proper window controls and close functionality
- Improved button visibility and interaction
- Added keyboard shortcuts (Ctrl+Q, Escape)
- Enhanced CLI interface
- Better error handling and user feedback
- Proper RPM packaging with system integration

* Mon Jun 16 2025 Desktop State Manager Team <dev@desktop-state-manager.org> - 1.0-1
- Initial release
- Basic desktop state save/restore functionality
- TilingShell integration
- Command-line interface

