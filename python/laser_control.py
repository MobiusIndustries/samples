"""
Cobolt Laser Control GUI
Built upon hello_laser.py serial communication code
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
from serial.tools import list_ports
import sys
import threading
import queue

class LaserControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cobolt Laser Control")
        self.serial = None
        self.command_queue = queue.Queue()
        self.is_connected = False

        # Create main frames
        self.setup_frame = ttk.LabelFrame(root, text="Serial Connection")
        self.setup_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.control_frame = ttk.LabelFrame(root, text="Laser Control")
        self.control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.output_frame = ttk.LabelFrame(root, text="Output Display")
        self.output_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")

        # Configure grid weights
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(1, weight=1)

        self.setup_connection_widgets()
        self.setup_control_widgets()
        self.setup_output_display()

    def setup_connection_widgets(self):
        # Port selection
        ttk.Label(self.setup_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_combo = ttk.Combobox(self.setup_frame, width=30)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Connect button
        self.connect_btn = ttk.Button(self.setup_frame, text="Connect", command=self.connect_laser)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Refresh ports button
        self.refresh_btn = ttk.Button(self.setup_frame, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.refresh_ports()

    def setup_control_widgets(self):
        # Basic controls
        basic_frame = ttk.LabelFrame(self.control_frame, text="Basic Controls")
        basic_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Button(basic_frame, text="Laser ON (l1)", command=lambda: self.send_command("l1")).pack(fill="x", padx=5, pady=2)
        ttk.Button(basic_frame, text="Laser OFF (l0)", command=lambda: self.send_command("l0")).pack(fill="x", padx=5, pady=2)
        ttk.Button(basic_frame, text="Force Autostart (@cob1)", command=lambda: self.send_command("@cob1")).pack(fill="x", padx=5, pady=2)
        
        # Status queries
        status_frame = ttk.LabelFrame(self.control_frame, text="Status Queries")
        status_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        ttk.Button(status_frame, text="Get Serial Number (sn?)", command=lambda: self.send_command("sn?")).pack(fill="x", padx=5, pady=2)
        ttk.Button(status_frame, text="Get Laser State (l?)", command=lambda: self.send_command("l?")).pack(fill="x", padx=5, pady=2)
        ttk.Button(status_frame, text="Get LED Status (leds?)", command=lambda: self.send_command("leds?")).pack(fill="x", padx=5, pady=2)
        ttk.Button(status_frame, text="Get Fault Status (f?)", command=lambda: self.send_command("f?")).pack(fill="x", padx=5, pady=2)
        
        # Current control
        current_frame = ttk.LabelFrame(self.control_frame, text="Current Control")
        current_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Button(current_frame, text="Get Current (i?)", command=lambda: self.send_command("i?")).pack(fill="x", padx=5, pady=2)
        
        current_set_frame = ttk.Frame(current_frame)
        current_set_frame.pack(fill="x", padx=5, pady=2)
        self.current_entry = ttk.Entry(current_set_frame, width=10)
        self.current_entry.pack(side="left", padx=2)
        ttk.Button(current_set_frame, text="Set Current (slc)", 
                  command=lambda: self.send_command(f"slc {self.current_entry.get()}")).pack(side="left", padx=2)

        # Additional controls can be added here as needed

    def setup_output_display(self):
        self.output_text = scrolledtext.ScrolledText(self.output_frame, width=50, height=20)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_ports(self):
        devices_found = list(list_ports.comports())
        self.port_combo['values'] = [f"{port.device} - {port.description}" for port in devices_found]
        if self.port_combo['values']:
            self.port_combo.current(0)

    def connect_laser(self):
        if not self.is_connected:
            try:
                port = self.port_combo.get().split(' - ')[0]
                self.serial = serial.Serial(port, 112500, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="Disconnect")
                self.output_text.insert("end", "Connected to laser.\n")
                
                # Start reading thread
                self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.read_thread.start()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            if self.serial:
                self.serial.close()
            self.is_connected = False
            self.connect_btn.config(text="Connect")
            self.output_text.insert("end", "Disconnected from laser.\n")

    def send_command(self, command):
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to the laser first.")
            return
        
        try:
            full_command = command + "\r\n"
            self.serial.write(full_command.encode('ascii'))
            self.output_text.insert("end", f"Sent: {command}\n")
            self.output_text.see("end")
        except Exception as e:
            messagebox.showerror("Command Error", str(e))

    def read_serial(self):
        while self.is_connected:
            try:
                if self.serial.in_waiting:
                    response = self.serial.readline().decode('ascii').strip()
                    self.output_text.insert("end", f"Received: {response}\n")
                    self.output_text.see("end")
            except Exception as e:
                print(f"Read error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserControlGUI(root)
    root.mainloop()