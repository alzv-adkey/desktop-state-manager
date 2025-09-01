#!/usr/bin/env python3

import os
import json
import subprocess
from datetime import datetime

def test_backend_script():
    """Test if the backend script exists and is executable"""
    script_path = os.path.expanduser("~/tilingshell-desktop-restore.sh")
    
    if not os.path.exists(script_path):
        print("❌ Backend script not found")
        return False
    
    if not os.access(script_path, os.X_OK):
        print("❌ Backend script not executable")
        return False
    
    print("✅ Backend script found and executable")
    return True

def test_config_directory():
    """Test if config directory can be created"""
    config_dir = os.path.expanduser("~/.config/desktop-restore")
    
    try:
        os.makedirs(config_dir, exist_ok=True)
        print("✅ Config directory accessible")
        return True
    except Exception as e:
        print(f"❌ Config directory error: {e}")
        return False

def test_gui_dependencies():
    """Test if GUI dependencies are available"""
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        gi.require_version('Adw', '1')
        from gi.repository import Gtk, Adw, Gio, GLib
        print("✅ GTK4 and Adwaita available")
        return True
    except ImportError as e:
        print(f"❌ GUI dependencies missing: {e}")
        print("Install with: sudo dnf install python3-gobject gtk4-devel libadwaita-devel")
        return False

def test_system_tools():
    """Test if required system tools are available"""
    tools = ['wmctrl', 'python3', 'gsettings']
    missing = []
    
    for tool in tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing tools: {', '.join(missing)}")
        print(f"Install with: sudo dnf install {' '.join(missing)}")
        return False
    else:
        print("✅ All required system tools available")
        return True

def create_sample_state():
    """Create a sample state file for testing"""
    config_dir = os.path.expanduser("~/.config/desktop-restore")
    state_file = os.path.join(config_dir, "desktop-state.json")
    
    sample_state = {
        "timestamp": datetime.now().isoformat(),
        "workspaces": {
            "count": 4,
            "current": 0,
            "layouts": []
        },
        "windows": [
            {
                "id": "0x12345",
                "title": "Sample Window",
                "class": "SampleApp",
                "x": 100,
                "y": 100,
                "width": 800,
                "height": 600,
                "desktop": 0
            }
        ],
        "applications": [
            {
                "name": "firefox",
                "command": "firefox",
                "pid": "1234"
            }
        ],
        "tilingshell": {}
    }
    
    try:
        with open(state_file, 'w') as f:
            json.dump(sample_state, f, indent=2)
        print(f"✅ Sample state file created at {state_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create sample state: {e}")
        return False

def main():
    print("Desktop State Manager - Component Test")
    print("=" * 40)
    
    tests = [
        ("Backend Script", test_backend_script),
        ("Config Directory", test_config_directory),
        ("GUI Dependencies", test_gui_dependencies),
        ("System Tools", test_system_tools),
        ("Sample State", create_sample_state)
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        results[name] = test_func()
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    if all_passed:
        print("\n🎉 Desktop State Manager is ready to use!")
        print("You can:")
        print("  • Run GUI: ./launch-desktop-manager.sh")
        print("  • Run from command line: ./tilingshell-desktop-restore.sh")
        print("  • Find in applications menu: Desktop State Manager")
    
    return all_passed

if __name__ == "__main__":
    main()

