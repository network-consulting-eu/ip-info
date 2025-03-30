#!/usr/bin/env python3
import gi
import subprocess
import time
import statistics
import re
from datetime import datetime
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

class NetworkQualityMonitor:
    def __init__(self):
        # Configuration parameters
        self.ping_target = "8.8.8.8"  # Google's DNS server
        self.ping_count = 10  # Number of pings to average
        self.update_interval = 60  # Update every 60 seconds
        self.history_size = 10  # Keep history of last 10 readings
        self.update_timer_id = None
        
        self.latency_history = []
        self.jitter_history = []
        self.last_update = "Never"
        self.menu = None
        
        # Create indicator with a proper icon path
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "network-quality",
            "nm-signal-100",  # Using a standard icon name
            AyatanaAppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        
        # Set initial label
        self.indicator.set_label("...", "Network Monitor")
        self.indicator.set_title("Network Quality Monitor")
        
        # Create the menu - it must be assigned to an instance variable
        # to prevent garbage collection
        self.menu = self.create_menu()
        self.indicator.set_menu(self.menu)
        
        # Schedule regular updates
        self.update_timer_id = GLib.timeout_add_seconds(self.update_interval, self.update_data)
        
        # Initial data fetch - with a small delay to let the UI initialize
        GLib.timeout_add(500, self.update_data)
        print(f"Initialization complete - timer ID: {self.update_timer_id}")

    def ping_server(self):
        """Run ping and parse results to get latency and jitter"""
        try:
            # Reduce ping count for faster response
            cmd = f"ping -c {self.ping_count} {self.ping_target}"
            print(f"Running ping command: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            # Check if ping was successful
            if result.returncode != 0:
                print(f"Ping command returned error code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return None, None
                
            # Extract ping times using regex
            ping_times = re.findall(r"time=(\d+\.\d+) ms", result.stdout)
            if not ping_times:
                print(f"No ping times found in output: {result.stdout}")
                return None, None
                
            # Convert to float
            ping_times = [float(time) for time in ping_times]
            
            # Calculate latency (average) and jitter (standard deviation)
            latency = sum(ping_times) / len(ping_times)
            
            # Calculate jitter only if we have more than one ping
            jitter = statistics.stdev(ping_times) if len(ping_times) > 1 else 0
            
            print(f"Ping successful: latency={latency:.1f}ms, jitter={jitter:.1f}ms")
            return latency, jitter
            
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            print(f"Ping error: {e}")
            return None, None

    def get_connection_type(self):
        """Get current connection type (Ethernet or WiFi)"""
        try:
            # Check for active network connections
            cmd = "nmcli -t -f TYPE,DEVICE,STATE connection show --active"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Parse output to find the active connection type
            for line in result.stdout.splitlines():
                parts = line.split(':')
                if len(parts) >= 3 and parts[2] == "activated":
                    conn_type = parts[0].lower()
                    if "wireless" in conn_type or "wifi" in conn_type:
                        return "WiFi"
                    elif "ethernet" in conn_type:
                        return "Ethernet"
            
            return "Unknown"
            
        except subprocess.SubprocessError as e:
            print(f"Error getting connection type: {e}")
            return "Unknown"

    def update_data(self):
        """Update latency and jitter data"""
        print("===============================================")
        print("Updating network data...")
        # Get connection type
        conn_type = self.get_connection_type()
        print(f"Connection type: {conn_type}")
        
        # Get latency and jitter
        latency, jitter = self.ping_server()
        
        # Update history
        if latency is not None and jitter is not None:
            print(f"Adding to history: latency={latency:.1f}, jitter={jitter:.1f}")
            self.latency_history.append(latency)
            self.jitter_history.append(jitter)
            print(f"History now has {len(self.latency_history)} entries")
            
            # Keep history within size limit
            if len(self.latency_history) > self.history_size:
                self.latency_history.pop(0)
            if len(self.jitter_history) > self.history_size:
                self.jitter_history.pop(0)
        else:
            print("No latency/jitter data to add to history")
        
        # Update last check time
        self.last_update = datetime.now().strftime("%H:%M:%S")
        print(f"Last update time set to: {self.last_update}")
        
        # Set appropriate icon and label
        self.update_icon_and_label(latency, jitter, conn_type)
        
        # Recreate and update the menu
        try:
            self.menu = self.create_menu()
            self.indicator.set_menu(self.menu)
            print("Menu updated successfully")
        except Exception as e:
            print(f"Error updating menu: {e}")
        
        print("Update complete")
        print("===============================================")
        
        # Continue the timer
        return True

    def update_icon_and_label(self, latency, jitter, conn_type):
        """Update icon and label based on connection quality"""
        # Set default values for error case
        icon = "nm-no-connection"
        label = "ERR"
        
        if latency is not None:
            # Format the latency for display
            label = f"{latency:.0f}ms"
            
            # Choose appropriate icon
            if latency < 50:
                # Excellent connection
                icon = "nm-signal-100" if conn_type == "WiFi" else "nm-device-wired"
            elif latency < 100:
                # Good connection
                icon = "nm-signal-75" if conn_type == "WiFi" else "nm-device-wired"
            elif latency < 200:
                # Fair connection
                icon = "nm-signal-50" if conn_type == "WiFi" else "nm-device-wired"
            else:
                # Poor connection
                icon = "nm-signal-25" if conn_type == "WiFi" else "nm-device-wired"
        
        # Update the indicator icon and label
        try:
            self.indicator.set_icon_full(icon, "Network Quality")
            self.indicator.set_label(label, "Network Quality")
            print(f"Icon and label updated: icon={icon}, label={label}")
        except Exception as e:
            print(f"Error updating icon/label: {e}")

    def refresh_now_clicked(self, widget):
        print("Refresh button clicked")
        self.update_data()

    def change_target_clicked(self, widget):
        print("Change target button clicked")
        self.show_target_dialog()

    def change_interval_clicked(self, widget):
        print("Change interval button clicked") 
        self.show_interval_dialog()

    def quit_clicked(self, widget):
        print("Quit button clicked")
        Gtk.main_quit()

    def create_menu(self):
        """Create the indicator menu with current data"""
        menu = Gtk.Menu()
        
        # Add connection type
        conn_type = self.get_connection_type()
        item = Gtk.MenuItem(label=f"Connection: {conn_type}")
        item.set_sensitive(False)
        menu.append(item)
        
        # Add current latency and jitter if available
        print(f"Checking history data - latency history: {len(self.latency_history)}, jitter history: {len(self.jitter_history)}")
        if self.latency_history and self.jitter_history:
            print(f"Creating menu with data: {self.latency_history[-1]:.1f}ms")
            current_latency = self.latency_history[-1]
            current_jitter = self.jitter_history[-1]
            
            # Quality rating based on latency and jitter
            quality = self.get_quality_rating(current_latency, current_jitter)
            print(f"Quality rating: {quality}")
            
            item = Gtk.MenuItem(label=f"Quality: {quality}")
            item.set_sensitive(False)
            menu.append(item)
            
            item = Gtk.MenuItem(label=f"Latency: {current_latency:.1f} ms")
            item.set_sensitive(False)
            menu.append(item)
            
            item = Gtk.MenuItem(label=f"Jitter: {current_jitter:.1f} ms")
            item.set_sensitive(False)
            menu.append(item)
            
            # Calculate averages
            avg_latency = sum(self.latency_history) / len(self.latency_history)
            avg_jitter = sum(self.jitter_history) / len(self.jitter_history)
            
            separator = Gtk.SeparatorMenuItem()
            menu.append(separator)
            
            item = Gtk.MenuItem(label=f"Avg Latency: {avg_latency:.1f} ms")
            item.set_sensitive(False)
            menu.append(item)
            
            item = Gtk.MenuItem(label=f"Avg Jitter: {avg_jitter:.1f} ms")
            item.set_sensitive(False)
            menu.append(item)
        else:
            print("No history data available for menu")
            item = Gtk.MenuItem(label="No data available")
            item.set_sensitive(False)
            menu.append(item)
        
        # Add last update time
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)
        
        item = Gtk.MenuItem(label=f"Last update: {self.last_update}")
        item.set_sensitive(False)
        menu.append(item)
        
        # Add ping target
        item = Gtk.MenuItem(label=f"Target: {self.ping_target}")
        item.set_sensitive(False)
        menu.append(item)
        
        # Add actions
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)
        
        # Add refresh button with correct handler
        item_refresh = Gtk.MenuItem(label='Refresh Now')
        item_refresh.connect('activate', self.refresh_now_clicked)
        menu.append(item_refresh)
        
        # Add preferences menu
        prefs_menu = Gtk.Menu()
        
        # Add target server option
        item_target = Gtk.MenuItem(label='Change Target Server')
        item_target.connect('activate', self.change_target_clicked)
        prefs_menu.append(item_target)
        
        # Add update interval option
        item_interval = Gtk.MenuItem(label='Change Update Interval')
        item_interval.connect('activate', self.change_interval_clicked)
        prefs_menu.append(item_interval)
        
        # Make sure submenu items are visible
        prefs_menu.show_all()
        
        item_prefs = Gtk.MenuItem(label='Preferences')
        item_prefs.set_submenu(prefs_menu)
        menu.append(item_prefs)
        
        # Add quit button
        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit_clicked)
        menu.append(item_quit)
        
        # Show all menu items
        menu.show_all()
        
        return menu

    def show_target_dialog(self):
        """Display dialog to change the ping target server"""
        dialog = Gtk.Dialog(title="Change Target Server",
                            parent=None,
                            flags=0)
        
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        dialog.set_default_size(350, 100)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        
        label = Gtk.Label(label="Enter a new ping target (IP or hostname):")
        box.add(label)
        
        entry = Gtk.Entry()
        entry.set_text(self.ping_target)
        box.add(entry)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_target = entry.get_text().strip()
            if new_target:
                print(f"Changing target from {self.ping_target} to {new_target}")
                self.ping_target = new_target
                self.update_data()
        
        dialog.destroy()

    def show_interval_dialog(self):
        """Display dialog to change the update interval"""
        dialog = Gtk.Dialog(title="Change Update Interval",
                            parent=None,
                            flags=0)
        
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        dialog.set_default_size(350, 100)
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        
        label = Gtk.Label(label="Enter update interval in seconds:")
        box.add(label)
        
        adjustment = Gtk.Adjustment(value=self.update_interval, lower=10, upper=600, step_increment=5)
        spin_button = Gtk.SpinButton()
        spin_button.set_adjustment(adjustment)
        box.add(spin_button)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_interval = spin_button.get_value_as_int()
            if new_interval >= 10:
                print(f"Changing update interval from {self.update_interval} to {new_interval} seconds")
                self.update_interval = new_interval
                
                # Remove old timer and create a new one
                if self.update_timer_id:
                    GLib.source_remove(self.update_timer_id)
                self.update_timer_id = GLib.timeout_add_seconds(self.update_interval, self.update_data)
        
        dialog.destroy()

    def get_quality_rating(self, latency, jitter):
        """Get a quality rating based on latency and jitter"""
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

if __name__ == "__main__":
    app = NetworkQualityMonitor()
    try:
        print("Network Quality Monitor started. Press Ctrl+C to quit.")
        Gtk.main()
    except KeyboardInterrupt:
        print("Shutting down...")