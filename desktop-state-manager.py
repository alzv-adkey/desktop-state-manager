#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk
import subprocess
import json
import os
import threading
from datetime import datetime

class DesktopStateManager(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.desktopstatemanager',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tilingshell-desktop-restore.sh")
        self.config_dir = os.path.expanduser("~/.config/desktop-restore")
        self.state_file = os.path.join(self.config_dir, "desktop-state.json")
        self.window = None
        
    def do_activate(self):
        if not self.window:
            self.window = DesktopStateWindow(application=self)
        self.window.present()
        
    def do_startup(self):
        Adw.Application.do_startup(self)
        
        # Set up CSS for better appearance
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        .dim-label {
            opacity: 0.7;
        }
        """)
        
        # Add CSS provider to default display
        try:
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
        except Exception as e:
            print(f"Warning: Could not load CSS: {e}")

class DesktopStateWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Desktop State Manager")
        self.set_default_size(600, 500)
        
        # Initialize paths
        self.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tilingshell-desktop-restore.sh")
        self.config_dir = os.path.expanduser("~/.config/desktop-restore")
        self.state_file = os.path.join(self.config_dir, "desktop-state.json")
        
        # Setup the main interface
        self.setup_ui()
        self.refresh_state_info()
        
    def setup_ui(self):
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        main_box.append(header_bar)
        
        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        header_bar.pack_end(menu_button)
        
        # Create menu
        menu = Gio.Menu()
        menu.append("About", "app.about")
        menu.append("Preferences", "app.preferences")
        menu_button.set_menu_model(menu)
        
        # Add actions
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.get_application().add_action(about_action)
        
        pref_action = Gio.SimpleAction.new("preferences", None)
        pref_action.connect("activate", self.on_preferences)
        self.get_application().add_action(pref_action)
        
        # Main content area with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.append(scrolled)
        
        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        scrolled.set_child(content_box)
        
        # Title and description
        title_label = Gtk.Label()
        title_label.set_markup("<big><b>Desktop State Manager</b></big>")
        title_label.set_halign(Gtk.Align.START)
        content_box.append(title_label)
        
        desc_label = Gtk.Label()
        desc_label.set_text("Save and restore your desktop layout, including virtual desktops, applications, and TilingShell configurations.")
        desc_label.set_wrap(True)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("dim-label")
        content_box.append(desc_label)
        
        # Current state info group
        self.state_group = Adw.PreferencesGroup()
        self.state_group.set_title("Current State")
        content_box.append(self.state_group)
        
        # State info row
        self.state_info_row = Adw.ActionRow()
        self.state_info_row.set_title("No saved state")
        self.state_info_row.set_subtitle("Save your current desktop state to get started")
        self.state_group.add(self.state_info_row)
        
        # Quick actions group
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title("Quick Actions")
        actions_group.set_description("Common desktop state management tasks")
        content_box.append(actions_group)
        
        # Save state button
        save_row = Adw.ActionRow()
        save_row.set_title("Save Current State")
        save_row.set_subtitle("Capture current desktop layout and applications")
        save_button = Gtk.Button.new_with_label("Save")
        save_button.set_valign(Gtk.Align.CENTER)
        save_button.set_hexpand(False)
        save_button.set_size_request(100, 40)
        save_button.add_css_class("suggested-action")
        save_button.set_sensitive(True)
        save_button.set_visible(True)
        save_button.connect("clicked", self.on_save_state)
        save_row.add_suffix(save_button)
        save_row.set_activatable_widget(save_button)
        actions_group.add(save_row)
        
        # Restore state button
        restore_row = Adw.ActionRow()
        restore_row.set_title("Restore Saved State")
        restore_row.set_subtitle("Restore previously saved desktop layout")
        self.restore_button = Gtk.Button.new_with_label("Restore")
        self.restore_button.set_valign(Gtk.Align.CENTER)
        self.restore_button.set_hexpand(False)
        self.restore_button.set_size_request(100, 40)
        self.restore_button.add_css_class("destructive-action")
        self.restore_button.set_sensitive(True)
        self.restore_button.set_visible(True)
        self.restore_button.connect("clicked", self.on_restore_state)
        restore_row.add_suffix(self.restore_button)
        restore_row.set_activatable_widget(self.restore_button)
        actions_group.add(restore_row)
        
        # Advanced options group
        advanced_group = Adw.PreferencesGroup()
        advanced_group.set_title("Advanced Options")
        content_box.append(advanced_group)
        
        # Auto-restore toggle
        auto_restore_row = Adw.ActionRow()
        auto_restore_row.set_title("Auto-restore on Login")
        auto_restore_row.set_subtitle("Automatically restore desktop state when you log in")
        self.auto_restore_switch = Gtk.Switch()
        self.auto_restore_switch.set_valign(Gtk.Align.CENTER)
        self.auto_restore_switch.connect("notify::active", self.on_auto_restore_toggle)
        auto_restore_row.add_suffix(self.auto_restore_switch)
        advanced_group.add(auto_restore_row)
        
        # TilingShell backup
        tiling_backup_row = Adw.ActionRow()
        tiling_backup_row.set_title("Backup TilingShell Config")
        tiling_backup_row.set_subtitle("Save only TilingShell tiling configurations")
        tiling_backup_button = Gtk.Button.new_with_label("Backup")
        tiling_backup_button.set_icon_name("folder-download-symbolic")
        tiling_backup_button.set_valign(Gtk.Align.CENTER)
        tiling_backup_button.set_size_request(80, 32)
        tiling_backup_button.set_sensitive(True)
        tiling_backup_button.set_visible(True)
        tiling_backup_button.connect("clicked", self.on_backup_tiling)
        tiling_backup_row.add_suffix(tiling_backup_button)
        advanced_group.add(tiling_backup_row)
        
        # TilingShell restore
        tiling_restore_row = Adw.ActionRow()
        tiling_restore_row.set_title("Restore TilingShell Config")
        tiling_restore_row.set_subtitle("Restore only TilingShell configurations")
        tiling_restore_button = Gtk.Button.new_with_label("Restore")
        tiling_restore_button.set_icon_name("folder-symbolic")
        tiling_restore_button.set_valign(Gtk.Align.CENTER)
        tiling_restore_button.set_size_request(80, 32)
        tiling_restore_button.set_sensitive(True)
        tiling_restore_button.set_visible(True)
        tiling_restore_button.connect("clicked", self.on_restore_tiling)
        tiling_restore_row.add_suffix(tiling_restore_button)
        advanced_group.add(tiling_restore_row)
        
        # Status and progress
        self.status_group = Adw.PreferencesGroup()
        self.status_group.set_title("Status")
        content_box.append(self.status_group)
        
        self.status_row = Adw.ActionRow()
        self.status_row.set_title("Ready")
        self.status_row.set_subtitle("Desktop State Manager is ready to use")
        self.status_group.add(self.status_row)
        
        # Progress bar (initially hidden)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        content_box.append(self.progress_bar)
        
    def refresh_state_info(self):
        """Update the state information display"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                timestamp = state.get('timestamp', 'Unknown')
                applications = state.get('applications', [])
                app_count = len(applications)
                window_count = len(state.get('windows', []))
                workspace_count = state.get('workspaces', {}).get('count', 0)
                
                # Count applications by package type
                package_counts = {'native': 0, 'snap': 0, 'flatpak': 0}
                for app in applications:
                    pkg_type = app.get('package_type', 'native')
                    if pkg_type in package_counts:
                        package_counts[pkg_type] += 1
                    else:
                        package_counts['native'] += 1
                
                # Parse timestamp for display
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = timestamp
                
                self.state_info_row.set_title(f"State saved on {time_str}")
                
                # Enhanced subtitle with package type breakdown
                subtitle_parts = []
                if app_count > 0:
                    app_breakdown = []
                    if package_counts['native'] > 0:
                        app_breakdown.append(f"{package_counts['native']} native")
                    if package_counts['snap'] > 0:
                        app_breakdown.append(f"{package_counts['snap']} snap")
                    if package_counts['flatpak'] > 0:
                        app_breakdown.append(f"{package_counts['flatpak']} flatpak")
                    
                    if app_breakdown:
                        subtitle_parts.append(f"{app_count} apps ({', '.join(app_breakdown)})")
                    else:
                        subtitle_parts.append(f"{app_count} applications")
                else:
                    subtitle_parts.append("No applications")
                    
                subtitle_parts.extend([f"{window_count} windows", f"{workspace_count} workspaces"])
                self.state_info_row.set_subtitle(", ".join(subtitle_parts))
                self.restore_button.set_sensitive(True)
                
            except Exception as e:
                self.state_info_row.set_title("Error reading saved state")
                self.state_info_row.set_subtitle(str(e))
                self.restore_button.set_sensitive(False)
        else:
            self.state_info_row.set_title("No saved state")
            self.state_info_row.set_subtitle("Save your current desktop state to get started")
            self.restore_button.set_sensitive(False)
            
        # Check auto-restore status
        service_file = os.path.expanduser("~/.config/systemd/user/desktop-restore.service")
        self.auto_restore_switch.set_active(os.path.exists(service_file))
    
    def run_script_command(self, command, callback=None):
        """Run a script command in a separate thread"""
        def run_in_thread():
            try:
                result = subprocess.run([self.script_path, command], 
                                      capture_output=True, text=True, timeout=30)
                GLib.idle_add(lambda: self.on_command_finished(result, callback))
            except subprocess.TimeoutExpired:
                GLib.idle_add(lambda: self.on_command_error("Command timed out", callback))
            except Exception as e:
                GLib.idle_add(lambda: self.on_command_error(str(e), callback))
        
        # Show progress
        self.progress_bar.set_visible(True)
        self.progress_bar.pulse()
        self.update_status("Running command...", f"Executing: {command}")
        
        # Start command in thread
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
        
        # Pulse progress bar
        def pulse_progress():
            if self.progress_bar.get_visible():
                self.progress_bar.pulse()
                return True
            return False
        GLib.timeout_add(100, pulse_progress)
    
    def on_command_finished(self, result, callback=None):
        """Handle command completion"""
        self.progress_bar.set_visible(False)
        
        if result.returncode == 0:
            self.update_status("Success", result.stdout.strip() or "Command completed successfully")
            if callback:
                callback(True, result.stdout)
        else:
            self.update_status("Error", result.stderr.strip() or "Command failed")
            if callback:
                callback(False, result.stderr)
                
        # Refresh state info after any command
        self.refresh_state_info()
    
    def on_command_error(self, error, callback=None):
        """Handle command error"""
        self.progress_bar.set_visible(False)
        self.update_status("Error", error)
        if callback:
            callback(False, error)
    
    def update_status(self, title, subtitle):
        """Update the status display"""
        self.status_row.set_title(title)
        self.status_row.set_subtitle(subtitle)
    
    def on_save_state(self, button):
        """Handle save state button click"""
        print("DEBUG: Save state button clicked!")
        def callback(success, output):
            if success:
                self.show_toast("Desktop state saved successfully")
            else:
                print(f"DEBUG: Save failed: {output}")
        
        self.run_script_command("save", callback)
    
    def on_restore_state(self, button):
        """Handle restore state button click"""
        print("DEBUG: Restore state button clicked!")
        def callback(success, output):
            if success:
                self.show_toast("Desktop state restored successfully")
            else:
                print(f"DEBUG: Restore failed: {output}")
        
        self.run_script_command("restore", callback)
    
    def on_backup_tiling(self, button):
        """Handle TilingShell backup button click"""
        print("DEBUG: Backup TilingShell button clicked!")
        def callback(success, output):
            if success:
                self.show_toast("TilingShell configuration backed up")
            else:
                print(f"DEBUG: Backup failed: {output}")
        
        self.run_script_command("backup-tiling", callback)
    
    def on_restore_tiling(self, button):
        """Handle TilingShell restore button click"""
        print("DEBUG: Restore TilingShell button clicked!")
        def callback(success, output):
            if success:
                self.show_toast("TilingShell configuration restored")
            else:
                print(f"DEBUG: Restore tiling failed: {output}")
        
        self.run_script_command("restore-tiling", callback)
    
    def on_auto_restore_toggle(self, switch, param):
        """Handle auto-restore toggle"""
        if switch.get_active():
            def callback(success, output):
                if success:
                    self.show_toast("Auto-restore enabled")
                else:
                    switch.set_active(False)
            
            self.run_script_command("session", callback)
        else:
            # Disable auto-restore
            try:
                subprocess.run(["systemctl", "--user", "disable", "desktop-restore.service"], 
                             check=True, capture_output=True)
                service_file = os.path.expanduser("~/.config/systemd/user/desktop-restore.service")
                if os.path.exists(service_file):
                    os.remove(service_file)
                self.show_toast("Auto-restore disabled")
            except Exception as e:
                self.update_status("Error", f"Failed to disable auto-restore: {e}")
                switch.set_active(True)
    
    def show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        
        # Create toast overlay if it doesn't exist
        if not hasattr(self, 'toast_overlay'):
            self.toast_overlay = Adw.ToastOverlay()
            current_child = self.get_content()
            self.set_content(self.toast_overlay)
            self.toast_overlay.set_child(current_child)
        
        self.toast_overlay.add_toast(toast)
    
    def on_about(self, action, param):
        """Show about dialog"""
        about_dialog = Adw.AboutWindow()
        about_dialog.set_transient_for(self)
        
        # Use modern API properties
        about_dialog.set_property("application-name", "Desktop State Manager")
        about_dialog.set_property("version", "1.0.0")
        about_dialog.set_property("developer-name", "Desktop State Manager")
        about_dialog.set_property("license-type", Gtk.License.GPL_3_0)
        about_dialog.set_property("comments", "Save and restore your desktop layout, applications, and TilingShell configurations")
        about_dialog.set_property("website", "https://github.com/desktop-state-manager")
        about_dialog.set_property("copyright", "© 2024 Desktop State Manager")
        
        about_dialog.present()
    
    def on_preferences(self, action, param):
        """Show preferences dialog"""
        dialog = Adw.PreferencesWindow()
        dialog.set_transient_for(self)
        dialog.set_title("Preferences")
        
        # General page
        page = Adw.PreferencesPage()
        page.set_title("General")
        page.set_icon_name("preferences-system-symbolic")
        dialog.add(page)
        
        # File locations group
        group = Adw.PreferencesGroup()
        group.set_title("File Locations")
        page.add(group)
        
        # Script location
        script_row = Adw.ActionRow()
        script_row.set_title("Script Location")
        script_row.set_subtitle(self.script_path)
        group.add(script_row)
        
        # Config directory
        config_row = Adw.ActionRow()
        config_row.set_title("Configuration Directory")
        config_row.set_subtitle(self.config_dir)
        group.add(config_row)
        
        dialog.present()

def main():
    import sys
    app = DesktopStateManager()
    try:
        return app.run(sys.argv)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 1
    except Exception as e:
        print(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

