#!/bin/bash

# Enhanced Desktop State Restoration Script for GNOME with TilingShell
# This script provides advanced saving and restoration of:
# - Virtual desktops and workspace layouts
# - Application windows and their exact positions
# - TilingShell tiling states and layouts
# - Window properties (maximized, minimized, etc.)

CONFIG_DIR="$HOME/.config/desktop-restore"
STATE_FILE="$CONFIG_DIR/desktop-state.json"
TILINGSHELL_CONFIG="$HOME/.config/tilingshell"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Function to check if TilingShell is available
check_tilingshell() {
    if ! gnome-extensions list --enabled | grep -q "tilingshell@ferrarodomenico.com"; then
        echo "Warning: TilingShell extension not found or not enabled"
        return 1
    fi
    return 0
}

# Function to save complete desktop state
save_desktop_state() {
    echo "Saving comprehensive desktop state..."
    
    # Create JSON structure for state
    cat > "$STATE_FILE" << 'EOF'
{
    "timestamp": "",
    "workspaces": {
        "count": 0,
        "current": 0,
        "layouts": []
    },
    "windows": [],
    "applications": [],
    "tilingshell": {}
}
EOF

    # Get current timestamp
    TIMESTAMP=$(date -Iseconds)
    
    # Get workspace information
    WORKSPACE_COUNT=$(gsettings get org.gnome.desktop.wm.preferences num-workspaces)
    CURRENT_WORKSPACE=$(wmctrl -d | grep '\\*' | cut -d' ' -f1)

    # Create a more comprehensive state file using Python for JSON handling
    python3 << EOF
import json
import subprocess
import os
from datetime import datetime

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def get_window_info():
    windows = []
    # Get window list with positions
    wmctrl_output = run_command("wmctrl -lG")
    for line in wmctrl_output.split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 7:
                window = {
                    "id": parts[0],
                    "desktop": int(parts[1]),
                    "x": int(parts[2]),
                    "y": int(parts[3]),
                    "width": int(parts[4]),
                    "height": int(parts[5]),
                    "title": " ".join(parts[7:]),
                    "class": ""
                }
                # Get window class
                class_output = run_command(f"xprop -id {parts[0]} WM_CLASS 2>/dev/null")
                if class_output:
                    window["class"] = class_output.split('=')[-1].strip().strip('"')
                windows.append(window)
    return windows

def get_applications():
    apps = []
    app_info = {}
    
    # Get all installed flatpak applications
    flatpak_apps = {}
    try:
        flatpak_output = run_command("flatpak list --app --columns=name,application")
        for line in flatpak_output.split('\n'):
            if line.strip() and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    flatpak_apps[parts[0].strip()] = parts[1].strip()
    except:
        pass
    
    # Get all installed snap applications
    snap_apps = {}
    try:
        snap_output = run_command("snap list")
        for line in snap_output.split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) > 0:
                    snap_name = parts[0]
                    snap_apps[snap_name] = snap_name
    except:
        pass
    
    # Get running processes and their command lines
    ps_output = run_command("ps aux")
    for line in ps_output.split('\n'):
        if 'grep' not in line and line.strip():
            parts = line.split(None, 10)  # Split into max 11 parts
            if len(parts) > 10:
                full_command = parts[10]
                pid = parts[1]
                
                # Skip obvious system processes but allow some important paths
                if any(skip in full_command for skip in ['kworker', '[', '/sbin/', '/usr/sbin/', 'systemd', 'dbus']):
                    continue
                    
                # Skip some gnome processes but keep useful ones
                if '/usr/libexec/' in full_command and not any(keep in full_command for keep in ['flatpak', 'evolution', 'gedit']):
                    continue
                
                # Skip helper/support processes that shouldn't be restored as separate applications
                helper_processes = [
                    'crashpad_handler', 'crash_handler', '_crashpad_', 
                    'zygote', 'gpu-process', 'utility', 'renderer',
                    'broker', 'sandbox', 'nacl_helper', 'plugin',
                    '--type=', 'chrome --type=', '/chrome --type=',
                    '/usr/bin/bwrap', '/bin/bash /app/'
                ]
                if any(helper in full_command for helper in helper_processes):
                    continue
                
                app_info = {
                    "pid": pid,
                    "command": full_command,
                    "package_type": "native",
                    "package_name": "",
                    "app_id": ""
                }
                
                # Determine application type and extract name
                if '/snap/' in full_command:
                    # Snap application
                    app_info["package_type"] = "snap"
                    snap_path_parts = full_command.split('/snap/')
                    if len(snap_path_parts) > 1:
                        snap_name = snap_path_parts[1].split('/')[0]
                        app_info["package_name"] = snap_name
                        app_info["name"] = snap_name
                        app_info["launch_command"] = f"snap run {snap_name}"
                        
                elif ('flatpak run' in full_command or '/var/lib/flatpak/' in full_command or 
                      '/app/' in full_command or any('/.var/app/' in full_command for _ in [1])):
                    # Flatpak application
                    app_info["package_type"] = "flatpak"
                    
                    # Method 1: Direct flatpak run command
                    if 'flatpak run' in full_command:
                        parts = full_command.split()
                        if 'run' in parts:
                            run_index = parts.index('run')
                            if run_index + 1 < len(parts):
                                app_id = parts[run_index + 1]
                                app_info["app_id"] = app_id
                                app_info["package_name"] = app_id
                                # Find friendly name from flatpak list
                                for name, fapp_id in flatpak_apps.items():
                                    if fapp_id == app_id:
                                        app_info["name"] = name
                                        break
                                else:
                                    app_info["name"] = app_id.split('.')[-1]
                                app_info["launch_command"] = f"flatpak run {app_id}"
                    
                    # Method 2: Look for app running from /app/ path (flatpak sandbox)
                    elif '/app/' in full_command:
                        # Extract app ID from the environment or check running processes
                        # Look for the flatpak app ID in the environment variables
                        pid = app_info["pid"]
                        environ_cmd = f"cat /proc/{pid}/environ 2>/dev/null | tr '\0' '\n' | grep FLATPAK_ID"
                        environ_output = run_command(environ_cmd)
                        
                        app_id = ""
                        if environ_output and 'FLATPAK_ID=' in environ_output:
                            app_id = environ_output.split('FLATPAK_ID=')[1].split('\n')[0].strip()
                        
                        # If we couldn't get app ID from environment, try to match from config path
                        if not app_id and '/.var/app/' in full_command:
                            # Extract from path like /.var/app/com.slack.Slack/
                            var_app_parts = full_command.split('/.var/app/')
                            if len(var_app_parts) > 1:
                                app_id_candidate = var_app_parts[1].split('/')[0]
                                if '.' in app_id_candidate:  # Looks like a proper app ID
                                    app_id = app_id_candidate
                        
                        # Enhanced fallback: try to match against known flatpaks by executable name or path
                        if not app_id:
                            executable_name = os.path.basename(full_command.split()[0]).lower()
                            # Common mappings for flatpak executables
                            executable_to_appid = {
                                'telegram': 'org.telegram.desktop',
                                'telegram-desktop': 'org.telegram.desktop',
                                'discord': 'com.discordapp.Discord',
                                'spotify': 'com.spotify.Client',
                                'code': 'com.visualstudio.code',
                                'gimp': 'org.gimp.GIMP',
                                'firefox': 'org.mozilla.firefox',
                                'chrome': 'com.google.Chrome',
                                'vlc': 'org.videolan.VLC',
                                'slack': 'com.slack.Slack'
                            }
                            
                            # Also check for specific path patterns
                            if '/app/extra/slack' in full_command:
                                app_id = 'com.slack.Slack'
                            elif executable_name in executable_to_appid:
                                potential_app_id = executable_to_appid[executable_name]
                                # Verify it's actually installed
                                if potential_app_id in flatpak_apps.values():
                                    app_id = potential_app_id
                        
                        if app_id:
                            app_info["app_id"] = app_id
                            app_info["package_name"] = app_id
                            # Find friendly name
                            for name, fapp_id in flatpak_apps.items():
                                if fapp_id == app_id:
                                    app_info["name"] = name
                                    break
                            else:
                                app_info["name"] = app_id.split('.')[-1]
                            app_info["launch_command"] = f"flatpak run {app_id}"
                        else:
                            # Final fallback: use executable name but mark as unknown
                            app_name = os.path.basename(full_command.split()[0])
                            app_info["name"] = f"{app_name} (flatpak)"
                            app_info["launch_command"] = "unknown"
                    
                    else:
                        # Other flatpak paths - try bwrap detection
                        if 'bwrap' in full_command and '--' in full_command:
                            # Extract app ID from bwrap command
                            bwrap_parts = full_command.split('--')
                            if len(bwrap_parts) > 1:
                                potential_app_id = bwrap_parts[-1].strip()
                                if '.' in potential_app_id and potential_app_id in flatpak_apps.values():
                                    app_info["app_id"] = potential_app_id
                                    app_info["package_name"] = potential_app_id
                                    # Find friendly name
                                    for name, fapp_id in flatpak_apps.items():
                                        if fapp_id == potential_app_id:
                                            app_info["name"] = name
                                            break
                                    else:
                                        app_info["name"] = potential_app_id.split('.')[-1]
                                    app_info["launch_command"] = f"flatpak run {potential_app_id}"
                                else:
                                    app_info["name"] = "flatpak-app"
                                    app_info["launch_command"] = "unknown"
                            else:
                                app_info["name"] = "flatpak-app"
                                app_info["launch_command"] = "unknown"
                        else:
                            app_info["name"] = "flatpak-app"
                            app_info["launch_command"] = "unknown"
                        
                elif any(gui_app in os.path.basename(full_command).lower() for gui_app in 
                        ['firefox', 'chrome', 'chromium', 'code', 'nautilus', 'gnome-terminal', 
                         'gedit', 'libreoffice', 'gimp', 'inkscape', 'blender', 'vlc', 'thunderbird',
                         'discord', 'slack', 'spotify', 'steam', 'wine', 'outlook']):
                    # Native GUI application (excluding Telegram which we handle specially)
                    app_info["package_type"] = "native"
                    app_name = os.path.basename(full_command.split()[0])
                    app_info["name"] = app_name
                    app_info["package_name"] = app_name
                    app_info["launch_command"] = app_name
                    
                else:
                    # Check if this is a GUI application that might be a Flatpak but not detected yet
                    # Look for bwrap processes in the system that might be related to this process
                    executable_name = os.path.basename(full_command.split()[0]).lower()
                    
                    # Special handling for Telegram and other Flatpak apps that appear as native processes
                    if executable_name == 'telegram':
                        # Check if there are bwrap processes for Telegram
                        bwrap_check = run_command("ps aux | grep 'bwrap.*Telegram' | grep -v grep")
                        if bwrap_check:
                            app_info["package_type"] = "flatpak"
                            app_info["app_id"] = "org.telegram.desktop"
                            app_info["package_name"] = "org.telegram.desktop"
                            app_info["name"] = "Telegram"
                            app_info["launch_command"] = "flatpak run org.telegram.desktop"
                        else:
                            # Native telegram
                            app_info["package_type"] = "native"
                            app_info["name"] = "Telegram"
                            app_info["package_name"] = "telegram"
                            app_info["launch_command"] = "telegram-desktop"
                    else:
                        # Check if there's a bwrap process for this executable
                        bwrap_check = run_command(f"ps aux | grep 'bwrap.*{executable_name}' | grep -v grep")
                        if bwrap_check:
                            # This might be a Flatpak application
                            app_info["package_type"] = "flatpak"
                            
                            # Try to extract app ID from bwrap command
                            app_id = ""
                            for bwrap_line in bwrap_check.split('\n'):
                                if '--' in bwrap_line:
                                    bwrap_parts = bwrap_line.split('--')
                                    if len(bwrap_parts) > 1:
                                        potential_app_id = bwrap_parts[-1].strip()
                                        # Check if it looks like a proper app ID and is installed
                                        if '.' in potential_app_id and potential_app_id in flatpak_apps.values():
                                            app_id = potential_app_id
                                            break
                            
                            if app_id:
                                app_info["app_id"] = app_id
                                app_info["package_name"] = app_id
                                # Find friendly name
                                for name, fapp_id in flatpak_apps.items():
                                    if fapp_id == app_id:
                                        app_info["name"] = name
                                        break
                                else:
                                    app_info["name"] = app_id.split('.')[-1]
                                app_info["launch_command"] = f"flatpak run {app_id}"
                            else:
                                # Use executable name but mark as flatpak
                                app_info["name"] = f"{executable_name} (flatpak)"
                                app_info["launch_command"] = "unknown"
                        else:
                            # Skip non-GUI applications
                            continue
                
                # Avoid duplicates
                if app_info.get("name") and app_info["name"] not in [app.get('name') for app in apps]:
                    apps.append(app_info)
    
    return apps
# Build state object
state = {
    "timestamp": datetime.now().isoformat(),
    "workspaces": {
        "count": int(run_command("gsettings get org.gnome.desktop.wm.preferences num-workspaces")),
        "current": int(run_command("wmctrl -d | grep '\\\\*' | cut -d' ' -f1") or "0"),
        "layouts": []
    },
    "windows": get_window_info(),
    "applications": get_applications(),
    "tilingshell": {}
}

# Save TilingShell configuration if available
tilingshell_config_path = os.path.expanduser("~/.config/tilingshell")
if os.path.exists(tilingshell_config_path):
    state["tilingshell"]["config_path"] = tilingshell_config_path
    # Note: TilingShell stores its state in dconf, we'd need to export that

# Write state to file
with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)

print(f"Desktop state saved to $STATE_FILE")
EOF

    echo "Desktop state saved successfully!"
}

# Function to restore desktop state
restore_desktop_state() {
    echo "Restoring desktop state..."
    
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "Error: No saved state found. Run 'save' command first."
        exit 1
    fi
    
    # Use Python to parse and restore state
    python3 << 'EOF'
import json
import subprocess
import time
import os

def run_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=False)
    except:
        pass

def run_command_output(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

# Load state
with open(os.path.expanduser("~/.config/desktop-restore/desktop-state.json"), "r") as f:
    state = json.load(f)

print("Loaded state from:", state["timestamp"])

# Restore workspace count
workspace_count = state["workspaces"]["count"]
print(f"Setting workspace count to {workspace_count}")
run_command(f"gsettings set org.gnome.desktop.wm.preferences num-workspaces {workspace_count}")

# Wait for workspaces to be created
time.sleep(3)

# Enhanced application restoration with package manager support
def restore_application(app):
    """Restore an application based on its package type"""
    try:
        app_name = app.get("name", "unknown")
        package_type = app.get("package_type", "native")
        
        print(f"Starting {app_name} ({package_type})...")
        
        if package_type == "snap":
            # Restore snap application
            package_name = app.get("package_name", "")
            if package_name:
                # Check if snap is still installed
                check_result = run_command_output(f"snap list {package_name} 2>/dev/null")
                if package_name in check_result:
                    run_command(f"nohup snap run {package_name} >/dev/null 2>&1 &")
                    return True
                else:
                    print(f"Warning: Snap package {package_name} is no longer installed")
                    return False
                    
        elif package_type == "flatpak":
            # Restore flatpak application
            app_id = app.get("app_id", "") or app.get("package_name", "")
            if app_id:
                # Check if flatpak is still installed
                check_result = run_command_output(f"flatpak list --app | grep {app_id}")
                if app_id in check_result:
                    run_command(f"nohup flatpak run {app_id} >/dev/null 2>&1 &")
                    return True
                else:
                    print(f"Warning: Flatpak application {app_id} is no longer installed")
                    return False
                    
        elif package_type == "native":
            # Restore native application
            # Try different command variations
            possible_commands = []
            
            # Use launch_command if available
            if app.get("launch_command"):
                possible_commands.append(app["launch_command"])
            
            # Add common command mappings
            command_mapping = {
                "firefox": ["firefox", "firefox-bin"],
                "chrome": ["google-chrome", "chrome", "chromium"],
                "chromium": ["chromium-browser", "chromium"],
                "code": ["code", "codium", "vscodium"],
                "gedit": ["gedit", "gnome-text-editor"],
                "nautilus": ["nautilus", "gnome-files"],
                "gnome-terminal": ["gnome-terminal", "terminal"],
                "libreoffice": ["libreoffice"],
                "gimp": ["gimp"],
                "vlc": ["vlc"],
                "thunderbird": ["thunderbird"],
                "telegram": ["telegram-desktop", "telegram"],
                "discord": ["discord"],
                "slack": ["slack"],
                "spotify": ["spotify"],
                "steam": ["steam"]
            }
            
            app_lower = app_name.lower()
            for key, commands in command_mapping.items():
                if key in app_lower:
                    possible_commands.extend(commands)
                    break
            
            # If no mapping found, try the app name directly
            if not possible_commands:
                possible_commands = [app_name, app_name.lower()]
            
            # Try each command until one works
            for cmd in possible_commands:
                if run_command_output(f"which {cmd} 2>/dev/null"):
                    run_command(f"nohup {cmd} >/dev/null 2>&1 &")
                    return True
            
            print(f"Warning: Could not find command for native application {app_name}")
            return False
            
    except Exception as e:
        print(f"Error restoring {app_name}: {e}")
        return False
    
    return False

# Start applications
print("Starting applications...")
restored_count = 0
restored_windows = []  # Tracking restored window classes
for app in state["applications"]:
    if restore_application(app):
        restored_count += 1
        time.sleep(2)  # Wait between app launches
        restored_windows.append(app.get("package_name", "").lower())

print(f"Successfully restored {restored_count} out of {len(state['applications'])} applications")

# Wait for applications to start
print("Waiting for applications to initialize...")
time.sleep(5)

# Get current window list for better matching
def get_current_windows():
    """Get current window list with IDs, classes, and titles"""
    windows = {}
    wmctrl_output = run_command_output("wmctrl -lx")
    for line in wmctrl_output.split('\n'):
        if line.strip():
            parts = line.split(None, 4)
            if len(parts) >= 5:
                window_id = parts[0]
                desktop = parts[1]
                window_class = parts[2]
                hostname = parts[3]
                title = parts[4] if len(parts) > 4 else ""
                windows[window_id] = {
                    'id': window_id,
                    'desktop': desktop,
                    'class': window_class,
                    'title': title
                }
    return windows

# Reapply TilingShell layout after applications are launched
def reapply_tiling_layout():
    """Applies the saved TilingShell layout to the windows"""
    # Restore the layout from dconf
    run_command("dconf load /org/gnome/shell/extensions/tilingshell/ < /home/az/.config/desktop-restore/tilingshell-settings.dconf")
    print("Reapplied TilingShell layout")

# Handle applications that were restored but don't have saved window positions
print("Checking for apps without saved window positions...")
restored_app_names = [app.get('name', '').lower() for app in state['applications']]
saved_window_classes = [window.get('class', '').lower() for window in state['windows']]

# Create a mapping of apps that don't have corresponding window positions
apps_without_windows = []
for app in state['applications']:
    app_name = app.get('name', '').lower()
    # Check if this app has a corresponding window in the saved state
    has_saved_window = False
    for window in state['windows']:
        window_class = window.get('class', '').lower()
        if (app_name in window_class or 
            (app_name == 'telegram' and 'telegram' in window_class) or
            (app_name == 'slack' and 'slack' in window_class) or
            (app_name in ['chrome', 'google-chrome'] and 'chrome' in window_class)):
            has_saved_window = True
            break
    
    if not has_saved_window:
        apps_without_windows.append(app)
        print(f"  App '{app.get('name', 'Unknown')}' has no saved window position")

if apps_without_windows:
    print(f"Found {len(apps_without_windows)} apps without saved window positions")
    
    # Handle apps without saved window positions by assigning them to specific desktops
    print("Assigning unpositioned apps to default desktops...")
    time.sleep(2)  # Give time for windows to appear
    
    # Reapply tiling layout before getting any new windows
    reapply_tiling_layout()
    
    # Get current windows again to find any new ones
    current_windows_after = get_current_windows()
    print(f"Found {len(current_windows_after)} total windows after app restoration")
    
    # Find windows that weren't positioned in the main loop
    unpositioned_windows = {}
    for window_id, window_info in current_windows_after.items():
        # Check if this window was already positioned
        was_positioned = False
        for saved_window in state['windows']:
            stored_class_parts = saved_window.get('class', '').split('"')
            stored_class_clean = ""
            if len(stored_class_parts) >= 2:
                stored_class_clean = stored_class_parts[1].lower()
            
            current_class_lower = window_info['class'].lower()
            if stored_class_clean and stored_class_clean in current_class_lower:
                was_positioned = True
                break
        
        if not was_positioned:
            unpositioned_windows[window_id] = window_info
            print(f"  Found unpositioned window: {window_info['title'][:40]}... (class: {window_info['class']})")
    
    # Assign unpositioned windows to appropriate desktops
    desktop_assignments = {
        'telegram': 3,  # Desktop 3 for Telegram
        'discord': 3,
        'spotify': 2,
        'code': 1,
        'calculator': 0
    }
    
    for window_id, window_info in unpositioned_windows.items():
        assigned_desktop = 0  # Default desktop
        window_class_lower = window_info['class'].lower()
        window_title_lower = window_info['title'].lower()
        
        # Try to determine which app this window belongs to
        for app_name, desktop in desktop_assignments.items():
            if (app_name in window_class_lower or 
                app_name in window_title_lower or
                (app_name == 'telegram' and ('telegram' in window_class_lower or 'telegram' in window_title_lower))):
                assigned_desktop = desktop
                print(f"  Assigning {app_name} window to desktop {assigned_desktop}")
                break
        
        # Move window to assigned desktop
        move_cmd = f"wmctrl -i -r {window_id} -t {assigned_desktop}"
        run_command(move_cmd)
        time.sleep(0.3)
        
        print(f"  ✓ Moved unpositioned window to desktop {assigned_desktop}: {window_info['title'][:30]}...")
        
else:
    print("All restored apps have saved window positions")

# Wait longer for all windows to be fully initialized after TilingShell layout
print("Waiting for TilingShell to apply layouts...")
time.sleep(5)

# Enhanced window positioning and desktop assignment with better search logic
print("Ensuring windows are on correct desktops...")

# Get current window list for better matching
def get_current_windows():
    """Get current window list with IDs, classes, and titles"""
    windows = {}
    wmctrl_output = run_command_output("wmctrl -lx")
    for line in wmctrl_output.split('\n'):
        if line.strip():
            parts = line.split(None, 4)
            if len(parts) >= 5:
                window_id = parts[0]
                desktop = parts[1]
                window_class = parts[2]
                hostname = parts[3]
                title = parts[4] if len(parts) > 4 else ""
                windows[window_id] = {
                    'id': window_id,
                    'desktop': desktop,
                    'class': window_class,
                    'title': title
                }
    return windows

current_windows = get_current_windows()
print(f"Found {len(current_windows)} current windows")

for window in state["windows"]:
    window_title = window["title"]
    window_class = window["class"]
    window_desktop = window["desktop"]
    window_x = window["x"]
    window_y = window["y"]
    window_width = window["width"]
    window_height = window["height"]
    
    print(f"Positioning window: {window_title[:40]}... (class: {window_class}) on desktop {window_desktop}")
    
    # Enhanced window matching strategy
    target_window_id = None
    match_score = 0
    
    # Extract class name from the stored format (e.g., "outlook-for-linux", "outlook-for-linux" -> "outlook-for-linux")
    stored_class_parts = window_class.split('"')
    stored_class_clean = ""
    if len(stored_class_parts) >= 2:
        # Get the first non-empty class part (usually the app identifier)
        for part in stored_class_parts:
            if part.strip() and part.strip() != ", " and part.strip() != ",":
                stored_class_clean = part.strip().lower()
                break
    
    # Try to find the best matching window
    for current_id, current_window in current_windows.items():
        current_score = 0
        
        # Score based on window class matching
        current_class_lower = current_window['class'].lower()
        if stored_class_clean and stored_class_clean in current_class_lower:
            current_score += 50
        
        # Score based on title similarity
        current_title = current_window['title']
        if window_title and current_title:
            # Check for key words in title
            title_words = window_title.lower().split()
            current_title_lower = current_title.lower()
            matching_words = sum(1 for word in title_words if len(word) > 3 and word in current_title_lower)
            current_score += matching_words * 10
            
            # Check for exact substring matches
            if window_title[:20].lower() in current_title_lower:
                current_score += 30
        
        # Prefer windows not on desktop 0 if the target isn't desktop 0
        if window_desktop != 0 and current_window['desktop'] != '0':
            current_score += 5
        
        if current_score > match_score:
            match_score = current_score
            target_window_id = current_id
    
    if target_window_id and match_score > 20:  # Minimum confidence threshold
        print(f"  Found matching window ID: {target_window_id} (score: {match_score})")
        
        # Move window to correct desktop using window ID
        move_cmd = f"wmctrl -i -r {target_window_id} -t {window_desktop}"
        run_command(move_cmd)
        time.sleep(0.5)
        
        # For specific cases where TilingShell doesn't restore positioning correctly,
        # apply manual positioning (especially for side-by-side layouts)
        needs_manual_positioning = (
            window_desktop == 2 and  # Desktop 2 has Outlook + Asana side by side
            ("outlook" in stored_class_clean or "asana" in stored_class_clean or
             "outlook-for-linux" in stored_class_clean or "asana-snap" in stored_class_clean)
        )
        
        if needs_manual_positioning:
            # Apply manual positioning for better tiling control with longer delays
            time.sleep(1)  # Give TilingShell time to settle first
            position_cmd = f"wmctrl -i -r {target_window_id} -e 0,{window_x},{window_y},{window_width},{window_height}"
            run_command(position_cmd)
            time.sleep(1)  # Additional time for positioning to take effect
            print(f"  ✓ Applied manual positioning for better tiling")
        else:
            # Let TilingShell handle positioning for other cases
            print(f"  ✓ Letting TilingShell handle positioning")
        
        print(f"  ✓ Positioned window: {current_windows[target_window_id]['title'][:30]}...")
        
        # Remove from current_windows to avoid duplicate matching
        del current_windows[target_window_id]
        
    else:
        print(f"  ⚠ Could not find reliable match for: {window_title[:40]}... (best score: {match_score})")
        
        # Fallback: try title-based search as before, but with class filter
        fallback_terms = [
            window_title[:30],
            window_title.split(' - ')[0] if ' - ' in window_title else window_title[:20],
            stored_class_clean if stored_class_clean else window_title.split(' ')[0]
        ]
        
        window_found = False
        for search_term in fallback_terms:
            if not search_term.strip():
                continue
            
            # Check if window exists before trying to move it
            check_result = run_command_output(f"wmctrl -l | grep -i '{search_term}'")
            if check_result:
                move_cmd = f"wmctrl -r '{search_term}' -t {window_desktop}"
                run_command(move_cmd)
                time.sleep(0.5)
                
                position_cmd = f"wmctrl -r '{search_term}' -e 0,{window_x},{window_y},{window_width},{window_height}"
                run_command(position_cmd)
                window_found = True
                print(f"  ✓ Fallback positioned: {search_term}")
                break
        
        if not window_found:
            print(f"  ❌ Failed to position: {window_title[:40]}...")
    
    time.sleep(0.2)  # Small delay between window operations

# Switch to original workspace
current_workspace = state["workspaces"]["current"]
print(f"Switching to workspace {current_workspace}")
run_command(f"wmctrl -s {current_workspace}")

print("Desktop state restoration complete!")
EOF
}

# Function to create session management with systemd user service
setup_session_management() {
    SERVICE_DIR="$HOME/.config/systemd/user"
    SERVICE_FILE="$SERVICE_DIR/desktop-restore.service"
    
    # Determine script path (RPM installation or development)
    SCRIPT_PATH="/usr/share/desktop-state-manager/tilingshell-desktop-restore.sh"
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        SCRIPT_PATH="$(realpath "$0")"
    fi
    
    mkdir -p "$SERVICE_DIR"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Desktop State Restoration Service
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=oneshot
Environment=DISPLAY=:0
Environment=WAYLAND_DISPLAY=wayland-0
ExecStartPre=/bin/sleep 15
ExecStart=$SCRIPT_PATH restore
RemainAfterExit=yes
Restart=no

[Install]
WantedBy=default.target
EOF

    # Enable the service
    systemctl --user daemon-reload
    systemctl --user enable desktop-restore.service
    
    echo "Systemd user service created and enabled"
    echo "Desktop state will be restored automatically on login"
}

# Function to backup current TilingShell configuration
backup_tilingshell_config() {
    if check_tilingshell; then
        echo "Backing up TilingShell configuration..."
        
        # Export TilingShell dconf settings
        dconf dump /org/gnome/shell/extensions/tilingshell/ > "$CONFIG_DIR/tilingshell-settings.dconf"
        
        # Copy any config files
        if [[ -d "$TILINGSHELL_CONFIG" ]]; then
            cp -r "$TILINGSHELL_CONFIG" "$CONFIG_DIR/tilingshell-backup"
        fi
        
        echo "TilingShell configuration backed up"
    fi
}

# Function to restore TilingShell configuration
restore_tilingshell_config() {
    if [[ -f "$CONFIG_DIR/tilingshell-settings.dconf" ]]; then
        echo "Restoring TilingShell configuration..."
        dconf load /org/gnome/shell/extensions/tilingshell/ < "$CONFIG_DIR/tilingshell-settings.dconf"
        
        if [[ -d "$CONFIG_DIR/tilingshell-backup" ]]; then
            cp -r "$CONFIG_DIR/tilingshell-backup"/* "$TILINGSHELL_CONFIG/" 2>/dev/null
        fi
        
        echo "TilingShell configuration restored"
    fi
}

# Function to install required dependencies
install_dependencies() {
    echo "Checking and installing required dependencies..."
    
    # Check for required tools
    MISSING_TOOLS=()
    
    if ! command -v wmctrl >/dev/null; then
        MISSING_TOOLS+=("wmctrl")
    fi
    
    if ! command -v python3 >/dev/null; then
        MISSING_TOOLS+=("python3")
    fi
    
    if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
        echo "Missing tools: ${MISSING_TOOLS[*]}"
        echo "Install them with: sudo dnf install ${MISSING_TOOLS[*]}"
        exit 1
    fi
    
    echo "All required dependencies are available"
}

# Main script logic
case "$1" in
    "save")
        install_dependencies
        backup_tilingshell_config
        save_desktop_state
        ;;
    "restore")
        install_dependencies
        restore_tilingshell_config
        restore_desktop_state
        ;;
    "session")
        setup_session_management
        ;;
    "backup-tiling")
        backup_tilingshell_config
        ;;
    "restore-tiling")
        restore_tilingshell_config
        ;;
    *)
        echo "Enhanced Desktop State Restoration with TilingShell Support"
        echo "Usage: $0 {save|restore|session|backup-tiling|restore-tiling}"
        echo ""
        echo "Commands:"
        echo "  save           - Save current complete desktop state"
        echo "  restore        - Restore previously saved desktop state"
        echo "  session        - Setup automatic restoration via systemd user service"
        echo "  backup-tiling  - Backup only TilingShell configuration"
        echo "  restore-tiling - Restore only TilingShell configuration"
        echo ""
        echo "Enhanced Features:"
        echo "- Saves exact window positions and sizes"
        echo "- Preserves TilingShell layouts and configurations"
        echo "- JSON-based state storage for better parsing"
        echo "- Systemd integration for reliable session restoration"
        echo ""
        echo "Workflow:"
        echo "1. Set up your desktop with applications and TilingShell layouts"
        echo "2. Run: $0 save"
        echo "3. Run: $0 session (for automatic restoration)"
        exit 1
        ;;
esac
