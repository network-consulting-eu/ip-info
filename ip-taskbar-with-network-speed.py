#!/usr/bin/env python3
import gi
import subprocess
import time
import threading
import os
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

# Dictionary to store previous network statistics for speed calculation
previous_stats = {}
# Timestamp of previous stats update
previous_time = time.time()

def get_local_ips():
    cmd = "ip -4 addr show | grep -v '127.0.0.1' | grep inet | awk '{print $2 \" (\" $NF \")\"}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def get_public_ip():
    try:
        cmd = "curl -s --connect-timeout 5 https://ifconfig.me || curl -s --connect-timeout 5 https://api.ipify.org"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Unable to get public IP"

def get_network_stats():
    """Read network statistics from /proc/net/dev"""
    stats = {}
    
    with open('/proc/net/dev', 'r') as f:
        # Skip the header lines
        f.readline()
        f.readline()
        
        for line in f:
            parts = line.strip().split(':')
            if len(parts) < 2:
                continue
                
            interface = parts[0].strip()
            if interface == 'lo':  # Skip loopback interface
                continue
                
            data = parts[1].split()
            if len(data) < 9:
                continue
                
            rx_bytes = int(data[0])
            tx_bytes = int(data[8])
            
            stats[interface] = {
                'rx': rx_bytes,
                'tx': tx_bytes
            }
    
    return stats

def format_speed(bytes_per_sec):
    """Format bytes per second into human-readable format"""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.1f} B/s"
    elif bytes_per_sec < 1024*1024:
        return f"{bytes_per_sec/1024:.1f} KB/s"
    else:
        return f"{bytes_per_sec/(1024*1024):.1f} MB/s"

def calculate_speeds():
    """Calculate the current network speeds for all interfaces"""
    global previous_stats, previous_time
    
    current_stats = get_network_stats()
    current_time = time.time()
    time_diff = current_time - previous_time
    
    speeds = {}
    
    if previous_stats and time_diff > 0:
        for interface, stats in current_stats.items():
            if interface in previous_stats:
                rx_diff = stats['rx'] - previous_stats[interface]['rx']
                tx_diff = stats['tx'] - previous_stats[interface]['tx']
                
                rx_speed = rx_diff / time_diff
                tx_speed = tx_diff / time_diff
                
                speeds[interface] = {
                    'rx_speed': format_speed(rx_speed),
                    'tx_speed': format_speed(tx_speed)
                }
    
    previous_stats = current_stats
    previous_time = current_time
    
    return speeds

def update_menu():
    menu = Gtk.Menu()
    
    # Add public IP
    public_ip = get_public_ip()
    if public_ip:
        item = Gtk.MenuItem(label=f"Public IP: {public_ip}")
        item.show()
        menu.append(item)
    
    # Add separator
    separator = Gtk.SeparatorMenuItem()
    separator.show()
    menu.append(separator)
    
    # Calculate current network speeds
    speeds = calculate_speeds()
    
    # Add local IPs with speeds
    local_ips = get_local_ips()
    for ip in local_ips:
        if ip:
            # Extract interface name from IP string
            parts = ip.split('(')
            if len(parts) > 1:
                interface = parts[1].rstrip(')')
                
                # Show IP address
                item = Gtk.MenuItem(label=f"Local: {ip}")
                item.show()
                menu.append(item)
                
                # Add speed information if available
                if interface in speeds:
                    speed_item = Gtk.MenuItem(label=f"  ↓ {speeds[interface]['rx_speed']} | ↑ {speeds[interface]['tx_speed']}")
                    speed_item.show()
                    menu.append(speed_item)
    
    # Add separator
    separator2 = Gtk.SeparatorMenuItem()
    separator2.show()
    menu.append(separator2)
    
    # Add refresh button
    item_refresh = Gtk.MenuItem(label='Refresh')
    item_refresh.connect('activate', lambda _: update_indicator())
    item_refresh.show()
    menu.append(item_refresh)
    
    # Add quit button
    item_quit = Gtk.MenuItem(label='Quit')
    item_quit.connect('activate', quit)
    item_quit.show()
    menu.append(item_quit)
    
    return menu

def quit(_):
    Gtk.main_quit()

# Create indicator
indicator = AyatanaAppIndicator3.Indicator.new(
    "ip-monitor",
    "network-workgroup-symbolic",
    AyatanaAppIndicator3.IndicatorCategory.SYSTEM_SERVICES
)
indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

def update_indicator():
    indicator.set_menu(update_menu())
    return True

# Set initial menu
update_indicator()

# Set up an update timer - update every 2 seconds for real-time monitoring
GLib.timeout_add_seconds(2, update_indicator)

# Start main loop
Gtk.main()