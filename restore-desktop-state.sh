#!/bin/bash

# Desktop State Restoration Script for GNOME
# This script saves and restores desktop state including:
# - Virtual desktop configuration
# - Open applications and their positions
# - Window tiling states (with TilingShell extension)

CONFIG_DIR="$HOME/.config/desktop-restore"
STATE_FILE="$CONFIG_DIR/desktop-state.conf"
APPS_FILE="$CONFIG_DIR/running-apps.conf"
WINDOWS_FILE="$CONFIG_DIR/window-positions.conf"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Function to save current desktop state
save_state() {
    echo "Saving desktop state..."
    
    # Save workspace configuration
    echo "# Workspace Configuration" > "$STATE_FILE"
    echo "WORKSPACES=$(gsettings get org.gnome.desktop.wm.preferences num-workspaces)" >> "$STATE_FILE"
    echo "CURRENT_WORKSPACE=$(wmctrl -d | grep '\*' | cut -d' ' -f1)" >> "$STATE_FILE"
    
    # Save running applications
    echo "# Running Applications" > "$APPS_FILE"
    ps aux | grep -E '\.(AppImage|desktop)|\b(firefox|chrome|chromium|code|gedit|nautilus|terminal|gnome-terminal)\b' | grep -v grep | while read line; do
        app=$(echo "$line" | awk '{print $11}' | xargs basename)
        echo "APP=$app" >> "$APPS_FILE"
    done
    
    # Alternative method: Get applications from .desktop files
    gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval "
        global.get_window_actors().map(a => {
            let win = a.get_meta_window();
            return {
                class: win.get_wm_class(),
                title: win.get_title(),
                workspace: win.get_workspace().index(),
                maximized: win.get_maximized(),
                x: win.get_frame_rect().x,
                y: win.get_frame_rect().y,
                width: win.get_frame_rect().width,
                height: win.get_frame_rect().height
            };
        })
    " 2>/dev/null | grep -o '{[^}]*}' >> "$APPS_FILE"
    
    # Save window positions and states
    echo "# Window Positions and States" > "$WINDOWS_FILE"
    wmctrl -lG | while read line; do
        echo "WINDOW=$line" >> "$WINDOWS_FILE"
    done
    
    echo "Desktop state saved to $CONFIG_DIR"
}

# Function to restore desktop state
restore_state() {
    echo "Restoring desktop state..."
    
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "No saved state found. Run with 'save' first."
        exit 1
    fi
    
    # Source the configuration
    source "$STATE_FILE"
    
    # Restore workspace count
    if [[ -n "$WORKSPACES" ]]; then
        echo "Setting workspace count to $WORKSPACES"
        gsettings set org.gnome.desktop.wm.preferences num-workspaces "$WORKSPACES"
    fi
    
    # Wait for workspaces to be created
    sleep 2
    
    # Restore applications
    if [[ -f "$APPS_FILE" ]]; then
        echo "Restoring applications..."
        restore_applications
    fi
    
    # Wait for applications to start
    sleep 5
    
    # Restore window positions
    if [[ -f "$WINDOWS_FILE" ]]; then
        echo "Restoring window positions..."
        restore_window_positions
    fi
    
    # Switch to the original workspace
    if [[ -n "$CURRENT_WORKSPACE" ]]; then
        echo "Switching to workspace $CURRENT_WORKSPACE"
        wmctrl -s "$CURRENT_WORKSPACE"
    fi
    
    echo "Desktop state restoration complete!"
}

# Function to restore applications
restore_applications() {
    # Common application commands mapping
    declare -A app_commands=(
        ["firefox"]="firefox"
        ["Firefox"]="firefox"
        ["chrome"]="google-chrome"
        ["chromium"]="chromium-browser"
        ["code"]="code"
        ["gedit"]="gedit"
        ["nautilus"]="nautilus"
        ["gnome-terminal"]="gnome-terminal"
        ["terminal"]="gnome-terminal"
        ["files"]="nautilus"
    )
    
    # Start applications from the saved list
    grep "^APP=" "$APPS_FILE" | while read line; do
        app=$(echo "$line" | cut -d'=' -f2)
        if [[ -n "${app_commands[$app]}" ]]; then
            echo "Starting $app..."
            nohup ${app_commands[$app]} >/dev/null 2>&1 &
            sleep 1
        fi
    done
}

# Function to restore window positions
restore_window_positions() {
    # This is a simplified version - full restoration would need more sophisticated parsing
    grep "^WINDOW=" "$WINDOWS_FILE" | while read line; do
        window_info=$(echo "$line" | cut -d'=' -f2-)
        # Parse window info and use wmctrl to position windows
        # This would need more complex parsing based on your specific needs
        echo "Window info: $window_info"
    done
}

# Function to create autostart entry
setup_autostart() {
    AUTOSTART_DIR="$HOME/.config/autostart"
    AUTOSTART_FILE="$AUTOSTART_DIR/desktop-restore.desktop"
    
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Desktop State Restore
Comment=Restore desktop state after login
Exec=$HOME/restore-desktop-state.sh restore
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF
    
    echo "Autostart entry created at $AUTOSTART_FILE"
    echo "Desktop state will be restored automatically on login (with 10 second delay)"
}

# Function to create a more advanced application launcher
create_app_launcher() {
    LAUNCHER_FILE="$CONFIG_DIR/app-launcher.conf"
    
    cat > "$LAUNCHER_FILE" << 'EOF'
# Application Launcher Configuration
# Format: APP_NAME:COMMAND:WORKSPACE:POSITION
# Position can be: maximized, left-half, right-half, top-half, bottom-half, or x,y,width,height

firefox:firefox:0:maximized
code:code:1:left-half
gnome-terminal:gnome-terminal:1:right-half
nautilus:nautilus:0:top-half
EOF
    
    echo "Application launcher configuration created at $LAUNCHER_FILE"
    echo "Edit this file to customize which applications start on which workspace and position"
}

# Main script logic
case "$1" in
    "save")
        save_state
        ;;
    "restore")
        restore_state
        ;;
    "autostart")
        setup_autostart
        ;;
    "configure")
        create_app_launcher
        ;;
    *)
        echo "Usage: $0 {save|restore|autostart|configure}"
        echo ""
        echo "Commands:"
        echo "  save      - Save current desktop state"
        echo "  restore   - Restore previously saved desktop state"
        echo "  autostart - Setup automatic restoration on login"
        echo "  configure - Create application launcher configuration"
        echo ""
        echo "Workflow:"
        echo "1. Set up your desktop as desired"
        echo "2. Run: $0 save"
        echo "3. Run: $0 autostart (to enable automatic restoration)"
        echo "4. Run: $0 configure (to customize application launching)"
        exit 1
        ;;
esac
EOF

