#!/bin/bash

# Desktop State Manager Launcher
# Simple script to launch the GUI application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_APP="$SCRIPT_DIR/desktop-state-manager.py"

# Check if the Python app exists
if [[ ! -f "$PYTHON_APP" ]]; then
    echo "Error: Desktop State Manager Python app not found at $PYTHON_APP"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."

# Check for Python3 and GTK
if ! command -v python3 >/dev/null; then
    echo "Error: Python3 not found. Please install python3."
    exit 1
fi

# Check for GTK4 and Adwaita
python3 -c "
import sys
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw
    print('✓ GTK4 and Adwaita libraries found')
except ImportError as e:
    print(f'✗ Missing GUI libraries: {e}')
    print('Please install: sudo dnf install python3-gobject gtk4-devel libadwaita-devel')
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    exit 1
fi

# Check for the backend script
BACKEND_SCRIPT="$SCRIPT_DIR/tilingshell-desktop-restore.sh"
if [[ ! -f "$BACKEND_SCRIPT" ]]; then
    echo "Warning: Backend script not found at $BACKEND_SCRIPT"
    echo "The GUI will work, but some functions may not be available."
fi

echo "✓ All dependencies satisfied"
echo "Launching Desktop State Manager..."

# Ensure proper display setup
if [[ -z "$DISPLAY" && -z "$WAYLAND_DISPLAY" ]]; then
    echo "Warning: No display environment detected"
    echo "Make sure you're running this from a graphical session"
fi

# Launch the application with proper error handling
cd "$SCRIPT_DIR"
if python3 "$PYTHON_APP" "$@"; then
    echo "✓ Desktop State Manager launched successfully"
else
    echo "✗ Failed to launch Desktop State Manager"
    echo "Check the error messages above for details"
    exit 1
fi

