#!/bin/bash

# Desktop State Manager - Command Line Interface
# Comprehensive CLI for managing desktop state without GUI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SCRIPT="$SCRIPT_DIR/tilingshell-desktop-restore.sh"
CONFIG_DIR="$HOME/.config/desktop-restore"
STATE_FILE="$CONFIG_DIR/desktop-state.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}   Desktop State Manager CLI${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_section() {
    echo
    echo -e "${PURPLE}>>> $1${NC}"
    echo "----------------------------------------"
}

# Check if backend script exists
check_backend() {
    if [[ ! -f "$BACKEND_SCRIPT" ]]; then
        print_error "Backend script not found at $BACKEND_SCRIPT"
        return 1
    fi
    
    if [[ ! -x "$BACKEND_SCRIPT" ]]; then
        print_error "Backend script is not executable"
        return 1
    fi
    
    return 0
}

# Show current desktop state information
show_status() {
    print_section "Current Desktop State"
    
    if [[ -f "$STATE_FILE" ]]; then
        if command -v jq >/dev/null 2>&1; then
            # Use jq for pretty formatting
            local timestamp=$(jq -r '.timestamp' "$STATE_FILE" 2>/dev/null)
            local workspace_count=$(jq -r '.workspaces.count' "$STATE_FILE" 2>/dev/null)
            local current_workspace=$(jq -r '.workspaces.current' "$STATE_FILE" 2>/dev/null)
            local window_count=$(jq -r '.windows | length' "$STATE_FILE" 2>/dev/null)
            local app_count=$(jq -r '.applications | length' "$STATE_FILE" 2>/dev/null)
            
            print_info "State saved: $timestamp"
            print_info "Workspaces: $workspace_count (current: $current_workspace)"
            print_info "Windows captured: $window_count"
            print_info "Applications: $app_count"
            
            echo
            echo "Recent applications captured:"
            jq -r '.applications[] | "  • " + .name + " (" + .command + ")"' "$STATE_FILE" 2>/dev/null | head -5
            
            echo
            echo "Windows by workspace:"
            jq -r '.windows[] | "  Workspace " + (.desktop|tostring) + ": " + .title' "$STATE_FILE" 2>/dev/null
            
        else
            print_info "State file exists: $STATE_FILE"
            print_warning "Install 'jq' for detailed state information: sudo dnf install jq"
        fi
    else
        print_warning "No saved state found"
        print_info "Run 'save' command to capture current desktop state"
    fi
}

# Save current desktop state
save_state() {
    print_section "Saving Desktop State"
    
    if ! check_backend; then
        return 1
    fi
    
    print_info "Capturing current desktop state..."
    if "$BACKEND_SCRIPT" save; then
        print_success "Desktop state saved successfully!"
        echo
        show_status
    else
        print_error "Failed to save desktop state"
        return 1
    fi
}

# Restore desktop state
restore_state() {
    print_section "Restoring Desktop State"
    
    if ! check_backend; then
        return 1
    fi
    
    if [[ ! -f "$STATE_FILE" ]]; then
        print_error "No saved state found. Save state first."
        return 1
    fi
    
    print_warning "This will modify your current desktop layout"
    echo -n "Continue? (y/N): "
    read -r confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_info "Restoring desktop state..."
        if "$BACKEND_SCRIPT" restore; then
            print_success "Desktop state restored successfully!"
        else
            print_error "Failed to restore desktop state"
            return 1
        fi
    else
        print_info "Restore cancelled"
    fi
}

# Setup auto-restore
setup_autostart() {
    print_section "Setting Up Auto-Restore"
    
    if ! check_backend; then
        return 1
    fi
    
    print_info "Setting up automatic restore on login..."
    if "$BACKEND_SCRIPT" session; then
        print_success "Auto-restore enabled!"
        print_info "Desktop state will be restored automatically on login"
    else
        print_error "Failed to setup auto-restore"
        return 1
    fi
}

# Check auto-restore status
check_autostart() {
    local service_file="$HOME/.config/systemd/user/desktop-restore.service"
    
    print_section "Auto-Restore Status"
    
    if [[ -f "$service_file" ]]; then
        print_success "Auto-restore is configured"
        
        # Check if service is enabled
        if systemctl --user is-enabled desktop-restore.service >/dev/null 2>&1; then
            print_success "Service is enabled"
        else
            print_warning "Service exists but is not enabled"
        fi
        
        # Show service status
        echo
        echo "Service file: $service_file"
        echo "Status: $(systemctl --user is-active desktop-restore.service 2>/dev/null || echo 'inactive')"
    else
        print_warning "Auto-restore is not configured"
        print_info "Run 'autostart' command to enable it"
    fi
}

# TilingShell management
manage_tilingshell() {
    print_section "TilingShell Management"
    
    if ! check_backend; then
        return 1
    fi
    
    echo "1) Backup TilingShell configuration"
    echo "2) Restore TilingShell configuration"
    echo "3) Back"
    echo
    echo -n "Choose an option (1-3): "
    read -r choice
    
    case $choice in
        1)
            print_info "Backing up TilingShell configuration..."
            if "$BACKEND_SCRIPT" backup-tiling; then
                print_success "TilingShell configuration backed up!"
            else
                print_error "Failed to backup TilingShell configuration"
            fi
            ;;
        2)
            print_info "Restoring TilingShell configuration..."
            if "$BACKEND_SCRIPT" restore-tiling; then
                print_success "TilingShell configuration restored!"
            else
                print_error "Failed to restore TilingShell configuration"
            fi
            ;;
        3)
            return 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Show system information
show_system_info() {
    print_section "System Information"
    
    echo "Desktop Environment: ${XDG_CURRENT_DESKTOP:-Unknown}"
    echo "Display: ${DISPLAY:-Not set}"
    echo "Session Type: ${XDG_SESSION_TYPE:-Unknown}"
    
    echo
    echo "Required tools:"
    for tool in wmctrl python3 gsettings jq; do
        if command -v $tool >/dev/null 2>&1; then
            print_success "$tool: Available"
        else
            print_error "$tool: Not found"
        fi
    done
    
    echo
    echo "GNOME Extensions:"
    if command -v gnome-extensions >/dev/null 2>&1; then
        if gnome-extensions list --enabled | grep -q "tilingshell"; then
            print_success "TilingShell: Enabled"
        else
            print_warning "TilingShell: Not found or disabled"
        fi
    else
        print_warning "Cannot check GNOME extensions"
    fi
}

# Show GUI application status
show_gui_status() {
    print_section "GUI Application Status"
    
    local desktop_file="$HOME/.local/share/applications/desktop-state-manager.desktop"
    local gui_script="$SCRIPT_DIR/desktop-state-manager.py"
    local launcher="$SCRIPT_DIR/launch-desktop-manager.sh"
    
    echo "GUI Components:"
    
    if [[ -f "$gui_script" ]]; then
        print_success "GUI Application: Available"
    else
        print_error "GUI Application: Missing"
    fi
    
    if [[ -f "$launcher" && -x "$launcher" ]]; then
        print_success "Launcher Script: Available"
    else
        print_error "Launcher Script: Missing or not executable"
    fi
    
    if [[ -f "$desktop_file" ]]; then
        print_success "Desktop Entry: Installed"
        print_info "Available in application menu as 'Desktop State Manager'"
    else
        print_error "Desktop Entry: Not installed"
    fi
    
    # Test GUI dependencies
    echo
    echo "GUI Dependencies:"
    if python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); from gi.repository import Gtk, Adw" 2>/dev/null; then
        print_success "GTK4 & Adwaita: Available"
        print_info "GUI can be launched with: ./launch-desktop-manager.sh"
    else
        print_error "GTK4 & Adwaita: Missing"
        print_info "Install with: sudo dnf install python3-gobject gtk4-devel libadwaita-devel"
    fi
}

# Main menu
show_menu() {
    clear
    print_header
    echo
    echo "Choose an action:"
    echo
    echo "1)  Show current status"
    echo "2)  Save desktop state"
    echo "3)  Restore desktop state"
    echo "4)  Setup auto-restore"
    echo "5)  Check auto-restore status"
    echo "6)  TilingShell management"
    echo "7)  Show system information"
    echo "8)  Show GUI application status"
    echo "9)  Quick test (save & show status)"
    echo "10) Exit"
    echo
}

# Quick test function
quick_test() {
    print_section "Quick Test"
    
    print_info "Running quick test of desktop state functionality..."
    echo
    
    # Save current state
    print_info "1. Saving current desktop state..."
    if "$BACKEND_SCRIPT" save >/dev/null 2>&1; then
        print_success "Save successful"
    else
        print_error "Save failed"
        return 1
    fi
    
    # Show what was captured
    echo
    print_info "2. Analyzing captured state..."
    show_status
    
    echo
    print_success "Quick test completed! Your desktop state is saved and ready."
}

# Main program
main() {
    if [[ $# -gt 0 ]]; then
        # Handle command line arguments
        case "$1" in
            "status"|"show")
                show_status
                ;;
            "save")
                save_state
                ;;
            "restore")
                restore_state
                ;;
            "autostart"|"session")
                setup_autostart
                ;;
            "check-autostart")
                check_autostart
                ;;
            "tiling")
                manage_tilingshell
                ;;
            "system"|"info")
                show_system_info
                ;;
            "gui")
                show_gui_status
                ;;
            "test")
                quick_test
                ;;
            *)
                echo "Usage: $0 [status|save|restore|autostart|check-autostart|tiling|system|gui|test]"
                exit 1
                ;;
        esac
    else
        # Interactive menu
        while true; do
            show_menu
            echo -n "Enter your choice (1-10): "
            read -r choice
            
            case $choice in
                1) show_status; echo; echo "Press Enter to continue..."; read ;;
                2) save_state; echo; echo "Press Enter to continue..."; read ;;
                3) restore_state; echo; echo "Press Enter to continue..."; read ;;
                4) setup_autostart; echo; echo "Press Enter to continue..."; read ;;
                5) check_autostart; echo; echo "Press Enter to continue..."; read ;;
                6) manage_tilingshell; echo; echo "Press Enter to continue..."; read ;;
                7) show_system_info; echo; echo "Press Enter to continue..."; read ;;
                8) show_gui_status; echo; echo "Press Enter to continue..."; read ;;
                9) quick_test; echo; echo "Press Enter to continue..."; read ;;
                10) echo "Goodbye!"; exit 0 ;;
                *) print_error "Invalid choice. Please try again."; sleep 1 ;;
            esac
        done
    fi
}

# Run main function
main "$@"

