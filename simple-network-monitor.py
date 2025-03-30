#!/usr/bin/env python3

import gi
import subprocess
import re
import statistics
from datetime import datetime
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

class SimpleNetworkMonitor:
    def __init__(self):
        self.ping_target = "8.8.8.8"
        self.ping_count = 5  # Reduced for speed
        self.update_interval = 10  # Quicker updates for testing
        
        # Create menu items
        self.connection_item = Gtk.MenuItem(label="Connection: Unknown")
        self.connection_item.set_sensitive(False)
        
        self.quality_item = Gtk.MenuItem(label="Quality: Unknown")
        self.quality_item.set_sensitive(False)
        
        self.latency_item = Gtk.MenuItem(label="Latency: Unknown")
        self.latency_item.set_sensitive(False)
        
        self.jitter_item = Gtk.MenuItem(label="Jitter: Unknown")
        self.jitter_item.set_sensitive(False)
        
        self.update_item = Gtk.MenuItem(label="Last update: Never")
        self.update_item.set_sensitive(False)
        
        self.target_item = Gtk.MenuItem(label=f"Target: {self.ping_target}")
        self.target_item.set_sensitive(False)
        
        # Create menu with fixed references to each item
        self.menu = Gtk.Menu()
        self.menu.append(self.connection_item)
        self.menu.append(self.quality_item)
        self.menu.append(self.latency_item)
        self.menu.append(self.jitter_item)
        
        separator1 = Gtk.SeparatorMenuItem()
        self.menu.append(separator1)
        
        self.menu.append(self.update_item)
        self.menu.append(self.target_item)
        
        separator2 = Gtk.SeparatorMenuItem()
        self.menu.append(separator2)
        
        refresh_item = Gtk.MenuItem(label="Refresh Now")
        refresh_item.connect('activate', self.refresh_clicked)
        self.menu.append(refresh_item)
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self.quit_clicked)
        self.menu.append(quit_item)
        
        self.menu.show_all()
        
        # Create indicator
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "simple-network-monitor",
            "nm-signal-100",
            AyatanaAppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu)
        self.indicator.set_label("...", "Network Monitor")
        
        # Initial update
        GLib.timeout_add(1000, self.update_data)
        
        # Regular updates
        GLib.timeout_add_seconds(self.update_interval, self.update_data)
    
    def get_ping_stats(self):
        try:
            cmd = f"ping -c {self.ping_count} {self.ping_target}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                print(f"Ping error: {result.stderr}")
                return None, None
            
            ping_times = re.findall(r"time=(\d+\.\d+) ms", result.stdout)
            if not ping_times:
                print("No ping times found")
                return None, None
            
            times = [float(t) for t in ping_times]
            latency = sum(times) / len(times)
            jitter = statistics.stdev(times) if len(times) > 1 else 0
            
            return latency, jitter
        
        except Exception as e:
            print(f"Error getting ping stats: {e}")
            return None, None
    
    def get_connection_type(self):
        try:
            result = subprocess.run(
                "nmcli -t -f TYPE,DEVICE,STATE connection show --active",
                shell=True, capture_output=True, text=True
            )
            
            for line in result.stdout.splitlines():
                parts = line.split(':')
                if len(parts) >= 3 and parts[2] == "activated":
                    conn_type = parts[0].lower()
                    if "wireless" in conn_type or "wifi" in conn_type:
                        return "WiFi"
                    elif "ethernet" in conn_type:
                        return "Ethernet"
            
            return "Unknown"
        
        except Exception:
            return "Unknown"
    
    def get_quality_rating(self, latency, jitter):
        if latency < 20 and jitter < 5:
            return "Excellent"
        elif latency < 50 and jitter < 10:
            return "Very Good"
        elif latency < 100 and jitter < 20:
            return "Good"
        elif latency < 150 and jitter < 30:
            return "Fair"
        elif latency < 200:
            return "Poor"
        else:
            return "Very Poor"
    
    def update_data(self):
        # Get connection type
        conn_type = self.get_connection_type()
        self.connection_item.set_label(f"Connection: {conn_type}")
        
        # Get ping stats
        latency, jitter = self.get_ping_stats()
        
        if latency is not None and jitter is not None:
            # Update menu items directly
            quality = self.get_quality_rating(latency, jitter)
            self.quality_item.set_label(f"Quality: {quality}")
            self.latency_item.set_label(f"Latency: {latency:.1f} ms")
            self.jitter_item.set_label(f"Jitter: {jitter:.1f} ms")
            
            # Update taskbar label
            self.indicator.set_label(f"{latency:.0f}ms", "Network Quality")
            
            # Update icon based on quality
            if latency < 50:
                icon = "nm-signal-100" if conn_type == "WiFi" else "nm-device-wired"
            elif latency < 100:
                icon = "nm-signal-75" if conn_type == "WiFi" else "nm-device-wired"
            elif latency < 200:
                icon = "nm-signal-50" if conn_type == "WiFi" else "nm-device-wired"
            else:
                icon = "nm-signal-25" if conn_type == "WiFi" else "nm-device-wired"
            
            self.indicator.set_icon_full(icon, "Network Quality")
            
            print(f"Updated menu with: latency={latency:.1f}ms, jitter={jitter:.1f}ms, quality={quality}")
        else:
            # Error state
            self.quality_item.set_label("Quality: Unknown")
            self.latency_item.set_label("Latency: Unknown")
            self.jitter_item.set_label("Jitter: Unknown")
            self.indicator.set_label("ERR", "Network Quality")
            self.indicator.set_icon_full("nm-no-connection", "Network Quality")
            
            print("Failed to get network stats")
        
        # Update last update time
        now = datetime.now().strftime("%H:%M:%S")
        self.update_item.set_label(f"Last update: {now}")
        
        return True
    
    def refresh_clicked(self, widget):
        print("Refresh clicked")
        self.update_data()
    
    def quit_clicked(self, widget):
        print("Quit clicked")
        Gtk.main_quit()

if __name__ == "__main__":
    monitor = SimpleNetworkMonitor()
    try:
        print("Simple Network Monitor started. Press Ctrl+C to quit.")
        Gtk.main()
    except KeyboardInterrupt:
        print("Shutting down...")