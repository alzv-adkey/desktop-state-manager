# Changelog

All notable changes to Desktop State Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Git repository with proper version control
- Contributing guidelines and development workflow
- GitHub Actions CI/CD pipeline
- Code quality checks and automated testing
- Changelog for tracking project history

### Changed
- Project now uses semantic versioning
- Improved development workflow with Git flow

## [3.4.0] - 2025-06-26
### Added
- CRITICAL FIX: TilingShell tiling restored correctly for side-by-side apps (Outlook, Asana)
- Enhanced manual positioning logic for better alignment
- CRITICAL FIX: Virtual desktop restoration now works correctly
- Enhanced window matching algorithm with confidence scoring
- Windows now properly restore to their original virtual desktops
- Improved window identification using window IDs instead of fragile title matching

### Fixed
- TilingShell tiling restoration for side-by-side applications
- Virtual desktop assignment - apps now restore to correct desktops
- Window matching reliability with confidence-based scoring
- Improved timing and delay handling between operations
- Enhanced fallback strategies for window positioning
- Fixed issue where all apps restored to single virtual desktop
- More reliable window class and title matching
- Better timing and stabilization for window operations

## [3.2.0] - 2025-06-26
### Added
- Enhanced application detection and restoration
- Comprehensive helper process filtering
- Better Flatpak app ID extraction from environment variables
- Improved bwrap process detection and handling

### Fixed
- MAJOR FIX: Chrome helper process duplication (no more extra windows)
- Improved Telegram detection as Flatpak application
- Enhanced Slack detection for /app/extra/ processes
- Fixed desktop assignment restoration
- All applications (Chrome, Slack, Telegram, Outlook) now restore correctly

## [2.0.0] - 2025-06-17
### Added
- Major rewrite with working GUI interface
- Proper window controls and close functionality
- Enhanced CLI interface
- Better error handling and user feedback
- Proper RPM packaging with system integration

### Changed
- Improved button visibility and interaction
- Added keyboard shortcuts (Ctrl+Q, Escape)

## [1.0.0] - 2025-06-16
### Added
- Initial release
- Basic desktop state save/restore functionality
- TilingShell integration
- Command-line interface
- Multi-package support: Native, Flatpak, and Snap applications
- Window positioning and virtual desktop management
- Systemd user service integration
- GTK4/Adwaita graphical interface

### Features
- Complete desktop state management
- Application window position and size preservation
- TilingShell layout backup and restoration
- Automatic restoration on login
- Both simple and advanced GUI interfaces
- Comprehensive CLI with interactive menus
- RPM packaging for easy installation
- Icon set with multiple resolutions

## Types of Changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
