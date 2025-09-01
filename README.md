# Desktop State Manager

A comprehensive desktop state management tool for GNOME with TilingShell support that allows you to save and restore your complete desktop layout, including applications, window positions, and TilingShell configurations.

## Features

- **Complete Desktop State Management**: Save and restore entire desktop layouts
- **Application Support**: 
  - Native applications
  - Flatpak applications (with proper app ID detection)
  - Snap packages
- **Window Management**: Preserve exact window positions and sizes
- **TilingShell Integration**: Backup and restore TilingShell tiling configurations
- **Session Management**: Automatic restoration on login via systemd
- **GUI Interface**: User-friendly GTK4/Adwaita interface

## Project Structure

```
desktop-state-manager/
├── README.md                              # This file
├── desktop-state-manager.py               # Main GUI application (full-featured)
├── desktop-state-manager-simple.py        # Simplified GUI version
├── tilingshell-desktop-restore.sh         # Core restoration script
├── desktop-cli.sh                         # Command-line interface
├── install-desktop-state-manager.sh       # Installation script
├── launch-desktop-manager.sh              # Launch helper
├── test-desktop-manager.py               # Testing utilities
├── restore-desktop-state.sh              # Legacy restore script
├── desktop-state-manager.desktop         # Desktop entry file
├── desktop-state-manager-fixed.desktop   # Fixed desktop entry
├── desktop-state-manager.spec            # RPM spec file
├── desktop-state-manager-2.0.tar.gz      # Source archive
└── desktop-state-manager-2.0-1.fc42.noarch.rpm  # Built RPM package
```

## Issues Identified and Fixed

### 1. Button Functionality Problems
- **Issue**: Buttons in some versions were not responding
- **Cause**: Complex threading and UI updates in the main version
- **Solution**: Use the simple version for better reliability, or the fixed main version

### 2. Flatpak/Snap Restoration Issues
- **Issue**: Snap and Flatpak applications were not being restored properly
- **Cause**: 
  - Incomplete app ID detection for Flatpak apps
  - Missing package name mapping
  - Regex syntax warnings in the shell script
- **Solution**: Enhanced detection logic that:
  - Properly identifies Flatpak app IDs from process environment
  - Maps application names to proper launch commands
  - Fixes regex syntax issues

### 3. Fixed Issues in Latest Version
- ✅ Fixed regex syntax warning (`grep '\\*'` → `grep '\\\\*'`)
- ✅ Enhanced Flatpak app ID detection from process environment variables
- ✅ Improved application restoration with proper package manager support
- ✅ Added fallback mechanisms for missing applications
- ✅ Better error handling and user feedback
- ✅ **NEW**: Auto-restore checkbox with systemd integration
- ✅ **NEW**: Enhanced window positioning on specific desktops
- ✅ **NEW**: Improved tiling restoration with proper timing

## Installation

### Method 1: RPM Package (Recommended for Fedora/Nobara)
```bash
sudo rpm -i desktop-state-manager-2.0-1.fc42.noarch.rpm
```

### Method 2: Manual Installation
```bash
chmod +x install-desktop-state-manager.sh
./install-desktop-state-manager.sh
```

### Method 3: Direct Usage
```bash
chmod +x desktop-state-manager-simple.py
chmod +x tilingshell-desktop-restore.sh
./desktop-state-manager-simple.py
```

## Usage

### GUI Applications

#### Simple Version (Recommended)
```bash
./desktop-state-manager-simple.py
```
- Clean, simple interface
- Reliable button functionality
- Direct feedback
- Test button for debugging

#### Full-Featured Version
```bash
./desktop-state-manager.py
```
- Advanced features
- Progress indicators
- Detailed status information
- Menu options

### Command Line Interface

#### Core Script
```bash
./tilingshell-desktop-restore.sh save      # Save current state
./tilingshell-desktop-restore.sh restore   # Restore saved state
./tilingshell-desktop-restore.sh session   # Setup auto-restore
```

#### CLI Wrapper
```bash
./desktop-cli.sh
```

## Configuration

The application stores its data in:
- Configuration: `~/.config/desktop-restore/`
- State file: `~/.config/desktop-restore/desktop-state.json`
- TilingShell backup: `~/.config/desktop-restore/tilingshell-settings.dconf`

## Dependencies

Required packages:
- `python3`
- `wmctrl`
- `gtk4`
- `libadwaita`
- `flatpak` (for Flatpak app restoration)
- `snapd` (for Snap app restoration)

Install on Fedora/Nobara:
```bash
sudo dnf install python3 wmctrl gtk4-devel libadwaita-devel python3-gobject
```

## Troubleshooting

### Buttons Not Working
- Use the simple version: `desktop-state-manager-simple.py`
- Check console output for debug messages
- Test with the debug button in simple version

### Flatpak Apps Not Restoring
- Ensure Flatpak apps are still installed: `flatpak list --app`
- Check the saved state file for proper app IDs
- Verify launch commands manually

### Snap Apps Not Restoring
- Ensure Snap packages are still installed: `snap list`
- Check snap service status: `systemctl status snapd`

### Window Positioning Issues
- Ensure `wmctrl` is installed and working
- Some applications may override window positioning
- TilingShell layouts take precedence over saved positions

## Development History

- **Initial Version**: Basic save/restore functionality
- **Version 1.x**: Added GUI interface, basic Flatpak support
- **Version 2.0**: Enhanced Flatpak/Snap detection, fixed button issues, improved error handling
- **Current**: Organized project structure, comprehensive documentation

## Contributing

1. Test the simple version first to verify basic functionality
2. Report issues with specific application types (native/flatpak/snap)
3. Check logs in `~/.config/desktop-restore/` for debugging
4. Submit improvements to the detection logic in `tilingshell-desktop-restore.sh`

## License

GPL-3.0 - See the application's About dialog for full license information.
