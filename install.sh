#!/bin/bash

# IP Information Tools Installer for Zorin OS
# This script installs the IP taskbar indicator and IP information dialog

echo "Installing IP Information Tools..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run with sudo: sudo $0"
  exit 1
fi

# Install required dependencies
echo "Installing required packages..."
apt update
apt install -y python3-gi gir1.2-ayatanaappindicator3-0.1 curl zenity

# Get the real user who ran sudo
REAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
REAL_HOME=$(getent passwd $REAL_USER | cut -d: -f6)

if [ -z "$REAL_USER" ] || [ -z "$REAL_HOME" ]; then
  echo "Error: Could not determine the real user. Please install manually."
  exit 1
fi

# Copy the scripts to /usr/local/bin
echo "Installing scripts..."
chmod +x ip-taskbar.py show-ip.sh
cp ip-taskbar.py /usr/local/bin/
cp show-ip.sh /usr/local/bin/

# Create desktop entries
echo "Creating desktop entries..."

# Create autostart entry for the taskbar indicator
mkdir -p $REAL_HOME/.config/autostart
cat > $REAL_HOME/.config/autostart/ip-taskbar.desktop << EOF
[Desktop Entry]
Type=Application
Name=IP Address Monitor
Comment=Shows local and public IP addresses in the system tray
Exec=/usr/local/bin/ip-taskbar.py
Icon=network-workgroup-symbolic
Terminal=false
Categories=Network;System;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

# Create application menu entry for the dialog
mkdir -p $REAL_HOME/.local/share/applications
cat > $REAL_HOME/.local/share/applications/show-ip.desktop << EOF
[Desktop Entry]
Type=Application
Name=IP Address Viewer
Comment=Shows local and public IP addresses
Exec=/usr/local/bin/show-ip.sh
Icon=network-workgroup
Terminal=false
Categories=Network;System;
EOF

# Fix permissions
chown -R $REAL_USER:$REAL_USER $REAL_HOME/.config/autostart/ip-taskbar.desktop
chown -R $REAL_USER:$REAL_USER $REAL_HOME/.local/share/applications/show-ip.desktop

echo "Starting IP taskbar indicator..."
sudo -u $REAL_USER /usr/local/bin/ip-taskbar.py &

echo "Installation complete!"
echo "The IP taskbar indicator is now running in your system tray."
echo "You can also find 'IP Address Viewer' in your applications menu."
echo ""
echo "To set up a keyboard shortcut (optional):"
echo "1. Go to Settings → Keyboard → Shortcuts → Custom Shortcuts"
echo "2. Click the '+' button"
echo "3. Name: IP Address Viewer"
echo "4. Command: show-ip.sh"
echo "5. Click 'Set Shortcut' and press your desired key combination (e.g., Ctrl+Alt+I)"