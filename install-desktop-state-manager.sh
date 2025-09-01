#!/bin/bash
# Desktop State Manager Installation Script
# Installs the Desktop State Manager RPM package

echo "🚀 Desktop State Manager Installation Script"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Do not run this script as root. It will ask for sudo when needed."
    exit 1
fi

# Check if RPM file exists
RPM_FILE="desktop-state-manager-2.0-1.fc42.noarch.rpm"
if [[ ! -f "$RPM_FILE" ]]; then
    echo "❌ Error: $RPM_FILE not found in current directory"
    echo "Make sure you're in the directory containing the RPM file"
    exit 1
fi

echo "📦 Found RPM package: $RPM_FILE"

# Check if already installed
if rpm -q desktop-state-manager >/dev/null 2>&1; then
    echo "🔄 Desktop State Manager is already installed. Upgrading..."
    sudo dnf upgrade -y "$RPM_FILE"
else
    echo "📥 Installing Desktop State Manager..."
    sudo dnf install -y "$RPM_FILE"
fi

# Check installation status
if rpm -q desktop-state-manager >/dev/null 2>&1; then
    echo "✅ Desktop State Manager installed successfully!"
    echo ""
    echo "🎯 How to use:"
    echo "  GUI Application:"
    echo "    • From Applications menu: Utilities → Desktop State Manager"
    echo "    • From command line: desktop-state-manager"
    echo ""
    echo "  Command Line Interface:"
    echo "    • Interactive menu: desktop-state-manager-cli"
    echo "    • Direct commands: desktop-state-manager-cli save|restore|status"
    echo ""
    echo "📁 Files installed:"
    echo "  • /usr/bin/desktop-state-manager - GUI launcher"
    echo "  • /usr/bin/desktop-state-manager-cli - CLI interface"
    echo "  • /usr/share/desktop-state-manager/ - Application files"
    echo "  • /usr/share/applications/desktop-state-manager.desktop - Menu entry"
    echo ""
    echo "🔧 Configuration stored in: ~/.config/desktop-restore/"
    echo ""
    echo "🎉 Installation complete! The app should now appear in your applications menu."
    
    # Update desktop database to ensure menu entry appears
    echo "🔄 Updating desktop database..."
    sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true
    
else
    echo "❌ Installation failed. Check the error messages above."
    exit 1
fi

