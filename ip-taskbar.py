#!/usr/bin/env python3
import gi
import subprocess
import time
import threading
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

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
    
    # Add local IPs
    local_ips = get_local_ips()
    for ip in local_ips:
        if ip:
            item = Gtk.MenuItem(label=f"Local: {ip}")
            item.show()
            menu.append(item)
    
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

# Set up an update timer
GLib.timeout_add_seconds(60, update_indicator)

# Start main loop
Gtk.main()