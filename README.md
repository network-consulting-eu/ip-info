# Network Information Tools for Zorin OS

This repository contains useful tools for displaying network information on Zorin OS (and other Ubuntu-based distributions):

1. **ip-taskbar.py** - A persistent system tray indicator that displays both local and public IP addresses
2. **show-ip.sh** - A lightweight dialog that can be triggered via keyboard shortcut to show IP information on demand
3. **network-quality.py** - A standalone application that monitors and displays network latency and jitter

## Tools Description

### IP Address Tools
The IP tools show your public IP address along with all local network interface IPs, making them ideal for system administrators, network troubleshooters, or anyone who needs to quickly check their connection details.

### Network Quality Monitor
The network quality monitor displays:
- Connection type (WiFi/Ethernet)
- Quality rating (Excellent, Very Good, Good, etc.)
- Current latency and jitter values
- Target server (defaulting to 8.8.8.8)
- Last update time

It includes auto-update functionality and allows you to change the target server for testing different connections.

## Requirements

These tools require the following packages:

```bash
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 curl zenity
```

## Installation

### Automatic Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/network-consulting-eu/ip-info.git
   cd ip-info
   ```

2. Run the installer script:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

### Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/network-consulting-eu/ip-info.git
   cd ip-info
   ```

2. Install dependencies:
   ```bash
   sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 curl zenity
   ```

3. Copy the scripts to a location in your PATH:
   ```bash
   chmod +x ip-taskbar.py show-ip.sh network-quality.py
   sudo cp ip-taskbar.py show-ip.sh network-quality.py /usr/local/bin/
   ```

4. Create a desktop entry for autostart:
   ```bash
   mkdir -p ~/.config/autostart
   cat > ~/.config/autostart/ip-taskbar.desktop << EOF
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
   ```

5. Create desktop entries for the application menu:
   ```bash
   mkdir -p ~/.local/share/applications
   
   # IP Address Viewer
   cat > ~/.local/share/applications/show-ip.desktop << EOF
   [Desktop Entry]
   Type=Application
   Name=IP Address Viewer
   Comment=Shows local and public IP addresses
   Exec=/usr/local/bin/show-ip.sh
   Icon=network-workgroup
   Terminal=false
   Categories=Network;System;
   EOF
   
   # Network Quality Monitor
   cat > ~/.local/share/applications/network-quality.desktop << EOF
   [Desktop Entry]
   Type=Application
   Name=Network Quality Monitor
   Comment=Monitors network latency and jitter
   Exec=/usr/local/bin/network-quality.py
   Icon=network-wireless
   Terminal=false
   Categories=Network;System;
   EOF
   ```

## Usage

### IP Taskbar Indicator

The IP taskbar indicator runs automatically after installation and shows up in your system tray. Click on it to view:

- Your public IP address
- All local IP addresses with their associated network interfaces
- Options to refresh the data or quit the application

The indicator updates automatically every minute.

To launch it manually (if not already running):
```bash
ip-taskbar.py
```

### IP Address Dialog

You can launch the IP address dialog in several ways:

1. From the application menu: Look for "IP Address Viewer" in your applications
2. From the command line:
   ```bash
   show-ip.sh
   ```
3. Set up a custom keyboard shortcut in Zorin OS:
   - Go to Settings → Keyboard → Shortcuts → Custom Shortcuts
   - Click the "+" button to add a new shortcut
   - Name: IP Address Viewer
   - Command: show-ip.sh
   - Click "Set Shortcut" and press your desired key combination (e.g., Ctrl+Alt+I)

### Network Quality Monitor

The Network Quality Monitor is a standalone application that shows detailed information about your network connection quality:

1. From the application menu: Look for "Network Quality Monitor" in your applications
2. From the command line:
   ```bash
   network-quality.py
   ```

The application allows you to:
- View real-time latency and jitter values
- See a quality rating based on these values
- Change the target server for testing
- Toggle automatic updates
- Refresh the data manually

## Troubleshooting

If the taskbar indicator doesn't appear:

1. Check if it's running:
   ```bash
   ps aux | grep ip-taskbar
   ```

2. Try running it from the terminal to see any error messages:
   ```bash
   ip-taskbar.py
   ```

3. Ensure the required packages are installed:
   ```bash
   sudo apt install --reinstall python3-gi gir1.2-ayatanaappindicator3-0.1 curl
   ```

If the dialog doesn't appear:

1. Make sure zenity is installed:
   ```bash
   sudo apt install zenity
   ```

2. Check if curl can access the internet:
   ```bash
   curl https://ifconfig.me
   ```

If the Network Quality Monitor doesn't work:

1. Run it from the terminal to see any error messages:
   ```bash
   network-quality.py
   ```

2. Verify you can ping the target server:
   ```bash
   ping -c 5 8.8.8.8
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.