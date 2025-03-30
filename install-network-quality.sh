#!/bin/bash

# Network Quality Monitor Installer for Zorin OS
# This script installs the Network Quality Monitor for tracking latency and jitter

echo "Installing Network Quality Monitor..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run with sudo: sudo $0"
  exit 1
fi

# Install required dependencies
echo "Installing required packages..."
apt update
apt install -y python3-gi gir1.2-ayatanaappindicator3-0.1

# Get the real user who ran sudo
REAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
REAL_HOME=$(getent passwd $REAL_USER | cut -d: -f6)

if [ -z "$REAL_USER" ] || [ -z "$REAL_HOME" ]; then
  echo "Error: Could not determine the real user. Please install manually."
  exit 1
fi

# Copy the script to /usr/local/bin
echo "Installing script..."
chmod +x network-quality.py
cp network-quality.py /usr/local/bin/

# Create desktop entry for autostart
echo "Creating autostart entry..."
mkdir -p $REAL_HOME/.config/autostart
cat > $REAL_HOME/.config/autostart/network-quality.desktop << EOF
[Desktop Entry]
Type=Application
Name=Network Quality Monitor
Comment=Monitors network latency and jitter
Exec=/usr/local/bin/network-quality.py
Icon=network-wireless-symbolic
Terminal=false
Categories=Network;System;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

# Fix permissions
chown -R $REAL_USER:$REAL_USER $REAL_HOME/.config/autostart/network-quality.desktop

echo "Starting Network Quality Monitor..."
sudo -u $REAL_USER /usr/local/bin/network-quality.py &

echo "Installation complete!"
echo "The Network Quality Monitor is now running in your system tray."
echo ""
echo "The monitor will:"
echo "- Ping 8.8.8.8 to check latency and jitter"
echo "- Update every 60 seconds"
echo "- Show quality rating in the taskbar"
echo ""
echo "You can change these settings by clicking on the indicator"
echo "and selecting 'Preferences' from the menu."