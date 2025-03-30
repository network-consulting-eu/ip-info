#!/usr/bin/env python3

import gi
import subprocess
import re
import time
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

class MinimalNetworkMonitor:
    def __init__(self):
        # Create indicator
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "minimal-network-monitor",
            "nm-signal-100",
            AyatanaAppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        
        # Set initial label (very important!)
        self.indicator.set_label("INIT", "Minimal Network Monitor")
        
        # Create a minimalist menu
        menu = Gtk.Menu()
        
        # Just a quit button
        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)
        
        menu.show_all()
        self.indicator.set_menu(menu)
        
        # Initial update
        GLib.timeout_add(1000, self.update_data)
        
        # Regular updates
        GLib.timeout_add_seconds(5, self.update_data)
    
    def get_ping_latency(self):
        try:
            cmd = "ping -c 3 8.8.8.8"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Ping error: {result.stderr}")
                return None
            
            ping_times = re.findall(r"time=(\d+\.\d+) ms", result.stdout)
            if not ping_times:
                print("No ping times found")
                return None
            
            times = [float(t) for t in ping_times]
            latency = int(sum(times) / len(times))
            
            return latency
            
        except Exception as e:
            print(f"Error getting ping stats: {e}")
            return None
    
    def update_data(self):
        # Get ping latency
        latency = self.get_ping_latency()
        
        current_time = time.strftime("%H:%M:%S")
        
        if latency is not None:
            # Update taskbar label with latency
            new_label = f"{latency}ms"
            self.indicator.set_label(new_label, "Network Latency")
            print(f"[{current_time}] Updated label to: {new_label}")
        else:
            # Error state
            self.indicator.set_label("ERR", "Network Error")
            print(f"[{current_time}] Failed to get ping latency")
        
        return True
    
    def quit(self, widget):
        Gtk.main_quit()

if __name__ == "__main__":
    monitor = MinimalNetworkMonitor()
    print("Minimal Network Monitor started. Press Ctrl+C to quit.")
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("Shutting down...")