#!/usr/bin/env python3
import gi
import subprocess
import statistics
import re
from datetime import datetime
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class NetworkInfoWindow:
    def __init__(self):
        # Configuration parameters
        self.ping_target = "8.8.8.8"  # Google's DNS server
        self.ping_count = 10  # Number of pings to average
        self.update_interval = 10  # Update every 10 seconds
        
        # Create the main window
        self.window = Gtk.Window(title="Network Quality Information")
        self.window.set_default_size(400, 300)
        self.window.set_border_width(10)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Create a vertical box for all content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(main_box)
        
        # Create info area with grid layout
        info_frame = Gtk.Frame(label="Network Status")
        main_box.pack_start(info_frame, True, True, 0)
        
        info_grid = Gtk.Grid()
        info_grid.set_column_spacing(10)
        info_grid.set_row_spacing(10)
        info_grid.set_margin_top(10)
        info_grid.set_margin_bottom(10)
        info_grid.set_margin_start(10)
        info_grid.set_margin_end(10)
        info_frame.add(info_grid)
        
        # Add labels for network information
        self.add_label_row(info_grid, 0, "Connection Type:", "Checking...")
        self.add_label_row(info_grid, 1, "Quality:", "Checking...")
        self.add_label_row(info_grid, 2, "Latency:", "Checking...")
        self.add_label_row(info_grid, 3, "Jitter:", "Checking...")
        self.add_label_row(info_grid, 4, "Target:", self.ping_target)
        self.add_label_row(info_grid, 5, "Last Update:", "Never")
        
        # Store references to value labels for updates
        self.conn_value_label = self.get_value_label(info_grid, 0)
        self.quality_value_label = self.get_value_label(info_grid, 1)
        self.latency_value_label = self.get_value_label(info_grid, 2)
        self.jitter_value_label = self.get_value_label(info_grid, 3)
        self.target_value_label = self.get_value_label(info_grid, 4)
        self.update_value_label = self.get_value_label(info_grid, 5)
        
        # Create action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(button_box, False, False, 0)
        
        # Refresh button
        refresh_button = Gtk.Button(label="Refresh Now")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        button_box.pack_start(refresh_button, True, True, 0)
        
        # Target change button
        target_button = Gtk.Button(label="Change Target")
        target_button.connect("clicked", self.on_change_target_clicked)
        button_box.pack_start(target_button, True, True, 0)
        
        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda w: Gtk.main_quit())
        button_box.pack_start(close_button, True, True, 0)
        
        # Auto-update toggle
        self.auto_update = True
        self.auto_update_switch = Gtk.Switch()
        self.auto_update_switch.set_active(True)
        self.auto_update_switch.connect("notify::active", self.on_switch_activated)
        
        auto_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_label = Gtk.Label(label="Auto-update:")
        auto_box.pack_start(auto_label, False, False, 0)
        auto_box.pack_start(self.auto_update_switch, False, False, 0)
        
        main_box.pack_start(auto_box, False, False, 0)
        
        # Timer for auto-updates
        self.update_timer_id = None
        
        # Show the window
        self.window.show_all()
        
        # Do initial update
        self.update_data()
        
        # Start auto-update timer
        self.update_timer_id = GLib.timeout_add_seconds(self.update_interval, self.update_data)
    
    def add_label_row(self, grid, row, title, value):
        """Add a row with title and value labels to the grid"""
        title_label = Gtk.Label(label=title, xalign=1)
        title_label.set_hexpand(True)
        title_label.set_halign(Gtk.Align.END)
        grid.attach(title_label, 0, row, 1, 1)
        
        value_label = Gtk.Label(label=value, xalign=0)
        value_label.set_hexpand(True)
        value_label.set_halign(Gtk.Align.START)
        grid.attach(value_label, 1, row, 1, 1)
    
    def get_value_label(self, grid, row):
        """Get the value label at the specified row"""
        # The value label is at position (1, row)
        return grid.get_child_at(1, row)
    
    def ping_server(self):
        """Run ping and parse results to get latency and jitter"""
        try:
            cmd = f"ping -c {self.ping_count} {self.ping_target}"
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
    
    def update_data(self):
        """Update network data and display"""
        print("Updating network data...")
        
        # Get connection type
        conn_type = self.get_connection_type()
        self.conn_value_label.set_text(conn_type)
        
        # Get latency and jitter
        latency, jitter = self.ping_server()
        
        if latency is not None and jitter is not None:
            # Update labels with network data
            quality = self.get_quality_rating(latency, jitter)
            self.quality_value_label.set_text(quality)
            self.latency_value_label.set_text(f"{latency:.1f} ms")
            self.jitter_value_label.set_text(f"{jitter:.1f} ms")
            print(f"Updated UI with: latency={latency:.1f}ms, jitter={jitter:.1f}ms, quality={quality}")
        else:
            # Error state
            self.quality_value_label.set_text("Error")
            self.latency_value_label.set_text("Error")
            self.jitter_value_label.set_text("Error")
            print("Failed to get network stats")
        
        # Update last check time
        self.update_value_label.set_text(datetime.now().strftime("%H:%M:%S"))
        
        # Return True to keep the timer going if auto-update is enabled
        return self.auto_update
    
    def on_refresh_clicked(self, button):
        """Handler for refresh button click"""
        print("Refresh button clicked")
        self.update_data()
    
    def on_change_target_clicked(self, button):
        """Handler for change target button click"""
        print("Change target button clicked")
        
        # Create dialog
        dialog = Gtk.Dialog(title="Change Target Server",
                            parent=self.window,
                            flags=0,
                            buttons=(
                                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OK, Gtk.ResponseType.OK
                            ))
        
        dialog.set_default_size(350, 100)
        
        # Create content area
        box = dialog.get_content_area()
        box.set_spacing(6)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Add label
        label = Gtk.Label(label="Enter a new ping target (IP or hostname):")
        box.add(label)
        
        # Add entry
        entry = Gtk.Entry()
        entry.set_text(self.ping_target)
        box.add(entry)
        
        dialog.show_all()
        
        # Run dialog
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_target = entry.get_text().strip()
            if new_target:
                print(f"Changing target from {self.ping_target} to {new_target}")
                self.ping_target = new_target
                self.target_value_label.set_text(new_target)
                self.update_data()
        
        dialog.destroy()
    
    def on_switch_activated(self, switch, gparam):
        """Handler for auto-update switch"""
        self.auto_update = switch.get_active()
        print(f"Auto-update {'enabled' if self.auto_update else 'disabled'}")
        
        # If turning on auto-update, start timer
        if self.auto_update and self.update_timer_id is None:
            self.update_timer_id = GLib.timeout_add_seconds(self.update_interval, self.update_data)
        # If turning off auto-update, stop timer
        elif not self.auto_update and self.update_timer_id is not None:
            GLib.source_remove(self.update_timer_id)
            self.update_timer_id = None

if __name__ == "__main__":
    app = NetworkInfoWindow()
    try:
        print("Network Info Window started. Close window to exit.")
        Gtk.main()
    except KeyboardInterrupt:
        print("Shutting down...")