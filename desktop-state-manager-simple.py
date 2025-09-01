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

class SimpleDesktopStateManager(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.simpledesktopstatemanager',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
    def do_activate(self):
        self.window = SimpleDesktopStateWindow(application=self)
        self.window.present()

class SimpleDesktopStateWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Desktop State Manager")
        self.set_default_size(500, 400)
        
        # Initialize paths
        # Try RPM installation path first, then development path
        rpm_script_path = "/usr/share/desktop-state-manager/tilingshell-desktop-restore.sh"
        dev_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tilingshell-desktop-restore.sh")
        
        if os.path.exists(rpm_script_path):
            self.script_path = rpm_script_path
        else:
            self.script_path = dev_script_path
        self.config_dir = os.path.expanduser("~/.config/desktop-restore")
        self.state_file = os.path.join(self.config_dir, "desktop-state.json")
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
    def setup_ui(self):
        # Main container with header bar
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)
        
        # Header bar with window controls
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="Desktop State Manager"))
        main_box.append(header_bar)
        
        # Add close button to header
        close_button = Gtk.Button()
        close_button.set_icon_name("window-close-symbolic")
        close_button.add_css_class("destructive-action")
        close_button.connect("clicked", self.on_close_clicked)
        header_bar.pack_end(close_button)
        
        # Add menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        header_bar.pack_end(menu_button)
        
        # Create simple menu
        menu = Gio.Menu()
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        menu_button.set_menu_model(menu)
        
        # Add menu actions
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_clicked)
        self.get_application().add_action(about_action)
        
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_clicked)
        self.get_application().add_action(quit_action)
        
        # Content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(30)
        content_box.set_margin_bottom(30)
        content_box.set_margin_start(30)
        content_box.set_margin_end(30)
        main_box.append(content_box)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Desktop State Manager</span>")
        title.set_halign(Gtk.Align.CENTER)
        content_box.append(title)
        
        # Description
        desc = Gtk.Label()
        desc.set_text("Save and restore your desktop layout and applications")
        desc.set_halign(Gtk.Align.CENTER)
        desc.add_css_class("dim-label")
        content_box.append(desc)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready")
        self.status_label.set_halign(Gtk.Align.CENTER)
        content_box.append(self.status_label)
        
        # Button container
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        button_box.set_halign(Gtk.Align.CENTER)
        content_box.append(button_box)
        
        # Save button
        self.save_button = Gtk.Button()
        self.save_button.set_label("💾 Save Desktop State")
        self.save_button.set_size_request(300, 50)
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self.on_save_clicked)
        button_box.append(self.save_button)
        
        # Restore button
        self.restore_button = Gtk.Button()
        self.restore_button.set_label("🔄 Restore Desktop State")
        self.restore_button.set_size_request(300, 50)
        self.restore_button.connect("clicked", self.on_restore_clicked)
        button_box.append(self.restore_button)
        
        # Test button for debugging
        test_button = Gtk.Button()
        test_button.set_label("🔧 Test Button")
        test_button.set_size_request(300, 50)
        test_button.connect("clicked", self.on_test_clicked)
        button_box.append(test_button)
        
        # Auto-restore checkbox
        auto_restore_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_restore_box.set_halign(Gtk.Align.CENTER)
        auto_restore_box.set_margin_top(20)
        
        self.auto_restore_checkbox = Gtk.CheckButton()
        self.auto_restore_checkbox.set_label("🔄 Auto-restore after reboot")
        self.auto_restore_checkbox.connect("toggled", self.on_auto_restore_toggled)
        auto_restore_box.append(self.auto_restore_checkbox)
        content_box.append(auto_restore_box)
        
        # Close button at bottom
        close_bottom_button = Gtk.Button()
        close_bottom_button.set_label("❌ Close Application")
        close_bottom_button.set_size_request(300, 40)
        close_bottom_button.add_css_class("destructive-action")
        close_bottom_button.connect("clicked", self.on_close_clicked)
        content_box.append(close_bottom_button)
        
        # Status info
        self.info_label = Gtk.Label()
        self.info_label.set_text("Click buttons above to manage your desktop state")
        self.info_label.set_halign(Gtk.Align.CENTER)
        self.info_label.set_wrap(True)
        content_box.append(self.info_label)
        
        # Update state info and auto-restore status
        self.update_state_info()
        self.update_auto_restore_status()
        
    def update_state_info(self):
        """Update the state information display"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                timestamp = state.get('timestamp', 'Unknown')
                app_count = len(state.get('applications', []))
                
                # Parse timestamp for display
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    time_str = timestamp
                
                self.info_label.set_text(f"Last saved: {time_str}\nApplications: {app_count}")
                self.restore_button.set_sensitive(True)
                
            except Exception as e:
                self.info_label.set_text(f"Error reading state: {e}")
                self.restore_button.set_sensitive(False)
        else:
            self.info_label.set_text("No saved state found")
            self.restore_button.set_sensitive(False)
    
    def on_save_clicked(self, button):
        """Handle save button click"""
        print("DEBUG: Save button clicked!")
        self.status_label.set_text("Saving desktop state...")
        button.set_sensitive(False)
        
        def run_save():
            try:
                result = subprocess.run([self.script_path, "save"], 
                                      capture_output=True, text=True, timeout=30)
                GLib.idle_add(self.on_save_finished, result, button)
            except Exception as e:
                GLib.idle_add(self.on_save_error, str(e), button)
        
        thread = threading.Thread(target=run_save)
        thread.daemon = True
        thread.start()
    
    def on_save_finished(self, result, button):
        """Handle save completion"""
        button.set_sensitive(True)
        if result.returncode == 0:
            self.status_label.set_text("✅ Desktop state saved successfully!")
            self.update_state_info()
        else:
            self.status_label.set_text(f"❌ Save failed: {result.stderr}")
        
        # Reset status after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))
    
    def on_save_error(self, error, button):
        """Handle save error"""
        button.set_sensitive(True)
        self.status_label.set_text(f"❌ Error: {error}")
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))
    
    def on_restore_clicked(self, button):
        """Handle restore button click"""
        print("DEBUG: Restore button clicked!")
        self.status_label.set_text("Restoring desktop state...")
        button.set_sensitive(False)
        
        def run_restore():
            try:
                result = subprocess.run([self.script_path, "restore"], 
                                      capture_output=True, text=True, timeout=30)
                GLib.idle_add(self.on_restore_finished, result, button)
            except Exception as e:
                GLib.idle_add(self.on_restore_error, str(e), button)
        
        thread = threading.Thread(target=run_restore)
        thread.daemon = True
        thread.start()
    
    def on_restore_finished(self, result, button):
        """Handle restore completion"""
        button.set_sensitive(True)
        if result.returncode == 0:
            self.status_label.set_text("✅ Desktop state restored successfully!")
        else:
            self.status_label.set_text(f"❌ Restore failed: {result.stderr}")
        
        # Reset status after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))
    
    def on_restore_error(self, error, button):
        """Handle restore error"""
        button.set_sensitive(True)
        self.status_label.set_text(f"❌ Error: {error}")
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))
    
    def on_test_clicked(self, button):
        """Handle test button click"""
        print("DEBUG: Test button clicked!")
        self.status_label.set_text("🎉 Test button works! Buttons are functional.")
        GLib.timeout_add_seconds(2, lambda: self.status_label.set_text("Ready"))
    
    def on_close_clicked(self, button):
        """Handle close button click"""
        print("DEBUG: Close button clicked!")
        self.close()
    
    def on_about_clicked(self, action, param):
        """Handle about menu item"""
        about_dialog = Adw.AboutWindow()
        about_dialog.set_transient_for(self)
        about_dialog.set_property("application-name", "Desktop State Manager")
        about_dialog.set_property("version", "2.0 (Fixed)")
        about_dialog.set_property("developer-name", "Desktop Tools")
        about_dialog.set_property("comments", "Save and restore your desktop layout with working buttons!")
        about_dialog.set_property("copyright", "© 2024 Desktop State Manager")
        about_dialog.present()
    
    def on_quit_clicked(self, action, param):
        """Handle quit menu item"""
        print("DEBUG: Quit menu clicked!")
        self.get_application().quit()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better window management"""
        # Create keyboard event controller
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts"""
        # Check for Ctrl+Q to quit
        if (state & Gtk.accelerator_get_default_mod_mask()) == Gtk.ModifierType.CONTROL_MASK:
            if keyval == Gdk.KEY_q:
                print("DEBUG: Ctrl+Q pressed, closing application")
                self.close()
                return True
        
        # Check for Escape to close
        if keyval == Gdk.KEY_Escape:
            print("DEBUG: Escape pressed, closing application")
            self.close()
            return True
            
        return False
    
    def update_auto_restore_status(self):
        """Update auto-restore checkbox status"""
        service_file = os.path.expanduser("~/.config/systemd/user/desktop-restore.service")
        is_enabled = os.path.exists(service_file)
        self.auto_restore_checkbox.set_active(is_enabled)
    
    def on_auto_restore_toggled(self, checkbox):
        """Handle auto-restore checkbox toggle"""
        print("DEBUG: Auto-restore checkbox toggled!")
        
        if checkbox.get_active():
            # Enable auto-restore
            self.status_label.set_text("Enabling auto-restore...")
            
            def run_enable():
                try:
                    result = subprocess.run([self.script_path, "session"], 
                                          capture_output=True, text=True, timeout=30)
                    GLib.idle_add(self.on_auto_restore_finished, result, True)
                except Exception as e:
                    GLib.idle_add(self.on_auto_restore_error, str(e), True)
            
            thread = threading.Thread(target=run_enable)
            thread.daemon = True
            thread.start()
        else:
            # Disable auto-restore
            self.status_label.set_text("Disabling auto-restore...")
            
            def run_disable():
                try:
                    # Disable systemd service
                    subprocess.run(["systemctl", "--user", "disable", "desktop-restore.service"], 
                                 check=False, capture_output=True)
                    
                    # Remove service file
                    service_file = os.path.expanduser("~/.config/systemd/user/desktop-restore.service")
                    if os.path.exists(service_file):
                        os.remove(service_file)
                    
                    # Reload systemd
                    subprocess.run(["systemctl", "--user", "daemon-reload"], 
                                 check=False, capture_output=True)
                    
                    GLib.idle_add(self.on_auto_restore_finished, type('Result', (), {'returncode': 0}), False)
                except Exception as e:
                    GLib.idle_add(self.on_auto_restore_error, str(e), False)
            
            thread = threading.Thread(target=run_disable)
            thread.daemon = True
            thread.start()
    
    def on_auto_restore_finished(self, result, enabled):
        """Handle auto-restore toggle completion"""
        if result.returncode == 0:
            if enabled:
                self.status_label.set_text("✅ Auto-restore enabled!")
            else:
                self.status_label.set_text("✅ Auto-restore disabled!")
            self.update_auto_restore_status()
        else:
            if enabled:
                self.status_label.set_text("❌ Failed to enable auto-restore")
                self.auto_restore_checkbox.set_active(False)
            else:
                self.status_label.set_text("❌ Failed to disable auto-restore")
                self.auto_restore_checkbox.set_active(True)
        
        # Reset status after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))
    
    def on_auto_restore_error(self, error, enabled):
        """Handle auto-restore toggle error"""
        self.status_label.set_text(f"❌ Auto-restore error: {error}")
        # Revert checkbox state
        self.auto_restore_checkbox.set_active(not enabled)
        GLib.timeout_add_seconds(3, lambda: self.status_label.set_text("Ready"))

def main():
    import sys
    app = SimpleDesktopStateManager()
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

