#!/usr/bin/env python3
import socket
import struct
import time
import sys
import argparse
import os
import signal
from datetime import datetime
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class MulticastTester:
    def __init__(self):
        # Create the main window
        self.window = Gtk.Window(title="Multicast Test Tool")
        self.window.set_default_size(500, 400)
        self.window.set_border_width(10)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(main_box)
        
        # Configuration Frame
        config_frame = Gtk.Frame(label="Multicast Configuration")
        main_box.pack_start(config_frame, False, False, 0)
        
        config_grid = Gtk.Grid()
        config_grid.set_column_spacing(10)
        config_grid.set_row_spacing(10)
        config_grid.set_margin_top(10)
        config_grid.set_margin_bottom(10)
        config_grid.set_margin_start(10)
        config_grid.set_margin_end(10)
        config_frame.add(config_grid)
        
        # Multicast group
        group_label = Gtk.Label(label="Multicast Group:", xalign=1)
        self.group_entry = Gtk.Entry()
        self.group_entry.set_text("239.192.11.1")
        config_grid.attach(group_label, 0, 0, 1, 1)
        config_grid.attach(self.group_entry, 1, 0, 1, 1)
        
        # Multicast port
        port_label = Gtk.Label(label="Multicast Port:", xalign=1)
        self.port_entry = Gtk.Entry()
        self.port_entry.set_text("1234")
        config_grid.attach(port_label, 0, 1, 1, 1)
        config_grid.attach(self.port_entry, 1, 1, 1, 1)
        
        # TTL
        ttl_label = Gtk.Label(label="TTL (min 15):", xalign=1)
        self.ttl_adjustment = Gtk.Adjustment(value=16, lower=15, upper=255, step_increment=1)
        self.ttl_spin = Gtk.SpinButton()
        self.ttl_spin.set_adjustment(self.ttl_adjustment)
        self.ttl_spin.set_numeric(True)
        config_grid.attach(ttl_label, 0, 2, 1, 1)
        config_grid.attach(self.ttl_spin, 1, 2, 1, 1)
        
        # Interface selection
        interface_label = Gtk.Label(label="Network Interface:", xalign=1)
        self.interface_combo = Gtk.ComboBoxText()
        
        # Populate interfaces
        interfaces = self.get_network_interfaces()
        for interface in interfaces:
            self.interface_combo.append_text(interface)
        if interfaces:
            self.interface_combo.set_active(0)
            
        config_grid.attach(interface_label, 0, 3, 1, 1)
        config_grid.attach(self.interface_combo, 1, 3, 1, 1)
        
        # Test duration
        duration_label = Gtk.Label(label="Test Duration (seconds):", xalign=1)
        self.duration_adjustment = Gtk.Adjustment(value=30, lower=5, upper=3600, step_increment=5)
        self.duration_spin = Gtk.SpinButton()
        self.duration_spin.set_adjustment(self.duration_adjustment)
        self.duration_spin.set_numeric(True)
        config_grid.attach(duration_label, 0, 4, 1, 1)
        config_grid.attach(self.duration_spin, 1, 4, 1, 1)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(button_box, False, False, 0)
        
        self.start_button = Gtk.Button(label="Start Test")
        self.start_button.connect("clicked", self.on_start_clicked)
        button_box.pack_start(self.start_button, True, True, 0)
        
        self.stop_button = Gtk.Button(label="Stop Test")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        self.stop_button.set_sensitive(False)
        button_box.pack_start(self.stop_button, True, True, 0)
        
        # Results area
        results_frame = Gtk.Frame(label="Test Results")
        main_box.pack_start(results_frame, True, True, 0)
        
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_hexpand(True)
        results_scroll.set_vexpand(True)
        results_frame.add(results_scroll)
        
        self.results_view = Gtk.TextView()
        self.results_view.set_editable(False)
        self.results_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.results_buffer = self.results_view.get_buffer()
        results_scroll.add(self.results_view)
        
        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.status_bar.push(0, "Ready")
        main_box.pack_start(self.status_bar, False, False, 0)
        
        # Variables to track the test
        self.is_running = False
        self.sock = None
        self.timeout_id = None
        self.packets_received = 0
        self.test_start_time = None
        self.multicast_socket = None
        
        # Show all widgets
        self.window.show_all()
    
    def get_network_interfaces(self):
        """Get list of network interfaces"""
        interfaces = []
        try:
            import netifaces
            interfaces = netifaces.interfaces()
        except ImportError:
            # Fallback method if netifaces is not available
            import subprocess
            try:
                output = subprocess.check_output("ip -o link show | awk -F': ' '{print $2}'", shell=True).decode('utf-8')
                interfaces = [line.strip() for line in output.splitlines() if line.strip()]
            except:
                # Last resort
                interfaces = ["eth0", "wlan0"]  # Common defaults
        
        return interfaces
    
    def log_message(self, message):
        """Add a message to the results view"""
        end_iter = self.results_buffer.get_end_iter()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_buffer.insert(end_iter, f"[{timestamp}] {message}\n")
        # Scroll to the end
        self.results_view.scroll_to_iter(self.results_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
    
    def update_status(self, message):
        """Update the status bar"""
        self.status_bar.pop(0)
        self.status_bar.push(0, message)
    
    def on_start_clicked(self, button):
        """Start the multicast test"""
        try:
            # Get configuration values
            mcast_group = self.group_entry.get_text()
            mcast_port = int(self.port_entry.get_text())
            ttl = self.ttl_spin.get_value_as_int()
            interface = self.interface_combo.get_active_text()
            duration = self.duration_spin.get_value_as_int()
            
            # Validate multicast address
            if not self.is_valid_multicast(mcast_group):
                self.log_message(f"Error: {mcast_group} is not a valid multicast address")
                return
            
            # Validate port
            if mcast_port < 1 or mcast_port > 65535:
                self.log_message("Error: Port must be between 1 and 65535")
                return
            
            # Update UI
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.group_entry.set_sensitive(False)
            self.port_entry.set_sensitive(False)
            self.ttl_spin.set_sensitive(False)
            self.interface_combo.set_sensitive(False)
            self.duration_spin.set_sensitive(False)
            
            # Reset counters
            self.packets_received = 0
            self.test_start_time = time.time()
            
            # Start the test
            self.is_running = True
            self.log_message(f"Starting multicast test...")
            self.log_message(f"Group: {mcast_group}, Port: {mcast_port}, TTL: {ttl}")
            self.log_message(f"Interface: {interface}, Duration: {duration} seconds")
            self.update_status("Test running...")
            
            # Create and set up the multicast socket
            self.create_multicast_socket(mcast_group, mcast_port, ttl, interface)
            
            # Set up a timer to check for received packets
            GLib.timeout_add(100, self.check_for_packets)
            
            # Set up a timer to end the test
            self.timeout_id = GLib.timeout_add_seconds(duration, self.end_test)
            
        except Exception as e:
            self.log_message(f"Error starting test: {str(e)}")
            self.reset_ui()
    
    def is_valid_multicast(self, address):
        """Check if an address is a valid multicast address"""
        try:
            # Parse the IP address
            octets = [int(octet) for octet in address.split('.')]
            if len(octets) != 4:
                return False
            
            # Check first octet for multicast range (224-239)
            return 224 <= octets[0] <= 239
        except:
            return False
    
    def create_multicast_socket(self, mcast_group, mcast_port, ttl, interface):
        """Create and set up the multicast socket"""
        try:
            # Create the socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Set TTL
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            
            # Bind to interface if specified
            if interface:
                try:
                    # Try to bind to the specific interface
                    import netifaces
                    addr = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                    self.sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(addr))
                    self.log_message(f"Bound to interface {interface} ({addr})")
                except (ImportError, KeyError, OSError) as e:
                    self.log_message(f"Warning: Could not bind to interface {interface}: {str(e)}")
            
            # Bind to the port
            self.sock.bind(('', mcast_port))
            
            # Join the multicast group
            mreq = struct.pack('4sl', socket.inet_aton(mcast_group), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Set non-blocking mode
            self.sock.setblocking(0)
            
            self.log_message("Multicast socket successfully created and joined group")
            
        except Exception as e:
            self.log_message(f"Socket error: {str(e)}")
            self.end_test()
    
    def check_for_packets(self):
        """Check if any multicast packets have been received"""
        if not self.is_running or not self.sock:
            return False
        
        try:
            # Try to receive a packet (non-blocking)
            try:
                data, addr = self.sock.recvfrom(1024)
                self.packets_received += 1
                
                # Log the first 10 packets in detail, then every 10th packet
                if self.packets_received <= 10 or self.packets_received % 10 == 0:
                    self.log_message(f"Received packet #{self.packets_received} from {addr[0]}:{addr[1]} ({len(data)} bytes)")
                
                # Update status bar more frequently
                elapsed = time.time() - self.test_start_time
                rate = self.packets_received / elapsed if elapsed > 0 else 0
                self.update_status(f"Running... Received {self.packets_received} packets ({rate:.2f} packets/sec)")
            except socket.error:
                # No data available, that's ok
                pass
            
        except Exception as e:
            self.log_message(f"Error receiving data: {str(e)}")
        
        # Continue checking
        return True
    
    def on_stop_clicked(self, button):
        """Stop the multicast test early"""
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        
        self.end_test()
    
    def end_test(self):
        """End the multicast test and clean up"""
        if not self.is_running:
            return False
        
        self.is_running = False
        
        # Clean up socket
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        # Calculate test results
        elapsed = time.time() - self.test_start_time if self.test_start_time else 0
        packets_per_second = self.packets_received / elapsed if elapsed > 0 else 0
        
        # Log results
        self.log_message("Test complete!")
        self.log_message(f"Duration: {elapsed:.2f} seconds")
        self.log_message(f"Total packets received: {self.packets_received}")
        self.log_message(f"Average rate: {packets_per_second:.2f} packets/second")
        
        # Update status
        self.update_status(f"Test complete. Received {self.packets_received} packets")
        
        # Reset UI
        self.reset_ui()
        
        return False
    
    def reset_ui(self):
        """Reset the UI after a test"""
        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.group_entry.set_sensitive(True)
        self.port_entry.set_sensitive(True)
        self.ttl_spin.set_sensitive(True)
        self.interface_combo.set_sensitive(True)
        self.duration_spin.set_sensitive(True)

def main():
    try:
        import netifaces
    except ImportError:
        print("Warning: netifaces module not found. Interface detection will be limited.")
        print("Install with: pip install netifaces")
    
    app = MulticastTester()
    Gtk.main()

if __name__ == "__main__":
    main()