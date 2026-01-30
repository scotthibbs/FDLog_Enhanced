"""
Hamlib rigctld Integration for FDLog Enhanced
Connects to rigctld TCP daemon to poll rig frequency/mode and push frequency changes.
No external dependencies — uses Python's built-in socket module.
"""

import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable

from wsjtx_integration import freq_to_band

# Reverse mapping: FDLog band string → default frequency in Hz
BAND_FREQ_MAP = {
    "160d": 1840000,
    "160c": 1840000,
    "160p": 1900000,
    "80d": 3573000,
    "80c": 3550000,
    "80p": 3900000,
    "40d": 7074000,
    "40c": 7050000,
    "40p": 7250000,
    "20d": 14074000,
    "20c": 14050000,
    "20p": 14250000,
    "15d": 21074000,
    "15c": 21050000,
    "15p": 21350000,
    "10d": 28074000,
    "10c": 28050000,
    "10p": 28400000,
    "6d": 50313000,
    "6c": 50100000,
    "6p": 50150000,
    "2d": 144174000,
    "2c": 144100000,
    "2p": 144200000,
    "220d": 432065000,
    "220c": 432100000,
    "220p": 432100000,
}

# rigctld mode → FDLog mode suffix
MODE_MAP = {
    "USB": "p",
    "LSB": "p",
    "AM": "p",
    "FM": "p",
    "CW": "c",
    "CWR": "c",
    "RTTY": "d",
    "RTTYR": "d",
    "PKTUSB": "d",
    "PKTLSB": "d",
    "PKT": "d",
    "DATA": "d",
    "DATAR": "d",
    "FMN": "p",
    "WFM": "p",
    "C4FM": "d",
    "DV": "d",
}


@dataclass
class RigctldConfig:
    """Configuration for rigctld integration."""
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 4532
    poll_interval: float = 2.0
    auto_band: bool = True
    push_frequency: bool = True


def parse_freq_response(data):
    """Parse frequency response from rigctld. Returns int Hz or None."""
    line = data.strip()
    if line.startswith("RPRT"):
        return None
    try:
        return int(line)
    except (ValueError, TypeError):
        return None


def parse_mode_response(data):
    """Parse mode response from rigctld. Returns (mode_str, passband_int) or None."""
    lines = data.strip().splitlines()
    if not lines or lines[0].startswith("RPRT"):
        return None
    mode = lines[0].strip()
    passband = 0
    if len(lines) > 1:
        try:
            passband = int(lines[1].strip())
        except (ValueError, TypeError):
            pass
    return mode, passband


def build_set_freq_command(freq_hz):
    """Build rigctld set frequency command."""
    return f"F {freq_hz}\n"


def build_set_mode_command(mode, passband=0):
    """Build rigctld set mode command."""
    return f"M {mode} {passband}\n"


def rigctld_mode_to_suffix(mode):
    """Map a rigctld mode string to FDLog mode suffix (c/p/d)."""
    return MODE_MAP.get(mode.upper(), "p")


class RigctldClient:
    """rigctld integration controller. Polls via TCP on a daemon thread."""

    _log_prefix = "rigctld"

    def __init__(self, config: RigctldConfig, on_status_update: Callable,
                 on_band_change: Optional[Callable] = None):
        self.config = config
        self.on_status_update = on_status_update
        self.on_band_change = on_band_change
        self._socket = None
        self._thread = None
        self._running = False
        self._connected = False
        self._current_freq = 0
        self._current_mode = ""
        self._current_band = None

    def start(self):
        """Start the TCP polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"{self._log_prefix}: Polling {self.config.host}:{self.config.port}")

    def stop(self):
        """Stop the polling thread."""
        self._running = False
        self._close_socket()
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._connected = False
        self.on_status_update("Disconnected")
        print(f"{self._log_prefix}: Client stopped")

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> dict:
        return {
            'connected': self._connected,
            'frequency': self._current_freq,
            'mode': self._current_mode,
            'running': self._running,
        }

    def set_frequency(self, freq_hz):
        """Send set frequency command to rigctld."""
        if not self._connected or not self._socket:
            return
        try:
            cmd = build_set_freq_command(freq_hz)
            self._socket.sendall(cmd.encode('ascii'))
            resp = self._recv_line()
            print(f"{self._log_prefix}: Set frequency to {freq_hz} Hz")
        except Exception as e:
            print(f"{self._log_prefix}: Failed to set frequency - {e}")
            self._handle_disconnect()

    def set_mode(self, mode, passband=0):
        """Send set mode command to rigctld."""
        if not self._connected or not self._socket:
            return
        try:
            cmd = build_set_mode_command(mode, passband)
            self._socket.sendall(cmd.encode('ascii'))
            resp = self._recv_line()
            print(f"{self._log_prefix}: Set mode to {mode}")
        except Exception as e:
            print(f"{self._log_prefix}: Failed to set mode - {e}")
            self._handle_disconnect()

    def _close_socket(self):
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _connect(self):
        """Attempt TCP connection to rigctld."""
        self._close_socket()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((self.config.host, self.config.port))
            s.settimeout(2.0)
            self._socket = s
            self._connected = True
            self.on_status_update("Connected")
            print(f"{self._log_prefix}: Connected to {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            self._close_socket()
            return False

    def _handle_disconnect(self):
        self._close_socket()
        if self._connected:
            self._connected = False
            self.on_status_update("Disconnected")
            print(f"{self._log_prefix}: Connection lost")

    def _recv_line(self):
        """Receive data from rigctld until newline."""
        data = b""
        while self._running:
            try:
                chunk = self._socket.recv(1024)
                if not chunk:
                    raise ConnectionError("Connection closed")
                data += chunk
                if b"\n" in data:
                    return data.decode('ascii', errors='replace')
            except socket.timeout:
                return data.decode('ascii', errors='replace') if data else ""
        return ""

    def _recv_mode_response(self):
        """Receive mode response (two lines: mode + passband)."""
        data = b""
        newline_count = 0
        while self._running:
            try:
                chunk = self._socket.recv(1024)
                if not chunk:
                    raise ConnectionError("Connection closed")
                data += chunk
                newline_count = data.count(b"\n")
                if newline_count >= 2 or (b"RPRT" in data and b"\n" in data):
                    return data.decode('ascii', errors='replace')
            except socket.timeout:
                return data.decode('ascii', errors='replace') if data else ""
        return ""

    def _poll_loop(self):
        backoff = 1.0
        while self._running:
            if not self._connected:
                if self._connect():
                    backoff = 1.0
                else:
                    time.sleep(min(backoff, 30.0))
                    backoff = min(backoff * 2, 30.0)
                    continue

            try:
                # Get frequency
                self._socket.sendall(b"f\n")
                freq_resp = self._recv_line()
                freq = parse_freq_response(freq_resp)

                # Get mode
                self._socket.sendall(b"m\n")
                mode_resp = self._recv_mode_response()
                mode_result = parse_mode_response(mode_resp)

                if freq is not None:
                    self._current_freq = freq
                if mode_result:
                    self._current_mode = mode_result[0]

                # Determine band
                if freq is not None:
                    suffix = rigctld_mode_to_suffix(self._current_mode) if self._current_mode else "p"
                    raw_band = freq_to_band(freq)
                    if raw_band:
                        # Replace the suffix from freq_to_band with the one from rig mode
                        band_prefix = raw_band[:-1]
                        band = band_prefix + suffix
                        mode_display = self._current_mode or "?"
                        self.on_status_update(f"Connected ({band_prefix}m {mode_display})")

                        if self.config.auto_band and band != self._current_band:
                            self._current_band = band
                            if self.on_band_change:
                                self.on_band_change(band)
                    else:
                        self.on_status_update(f"Connected ({freq} Hz)")

            except Exception:
                self._handle_disconnect()
                continue

            time.sleep(self.config.poll_interval)


# --- Settings Dialog ---

try:
    import tkinter as tk
    from tkinter import ttk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class RigctldSettingsDialog:
    """Tkinter dialog for rigctld integration settings."""

    def __init__(self, parent, config: RigctldConfig, client: Optional[RigctldClient], on_save: Callable):
        if not _TK_AVAILABLE:
            return
        self.config = config
        self.client = client
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("Rig Control (rigctld) Settings")
        self.win.geometry("400x350")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Enable/disable
        self.enabled_var = tk.BooleanVar(value=config.enabled)
        ttk.Checkbutton(frame, text="Enable rigctld Integration", variable=self.enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Host
        ttk.Label(frame, text="rigctld Host:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.host_var = tk.StringVar(value=config.host)
        ttk.Entry(frame, textvariable=self.host_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=3)

        # Port
        ttk.Label(frame, text="rigctld Port:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value=str(config.port))
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=3)

        # Poll interval
        ttk.Label(frame, text="Poll Interval (s):").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.poll_var = tk.StringVar(value=str(config.poll_interval))
        ttk.Entry(frame, textvariable=self.poll_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=3)

        # Auto-band
        self.auto_band_var = tk.BooleanVar(value=config.auto_band)
        ttk.Checkbutton(frame, text="Auto-switch band to match rig", variable=self.auto_band_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Push frequency
        self.push_freq_var = tk.BooleanVar(value=config.push_frequency)
        ttk.Checkbutton(frame, text="Push frequency changes to rig", variable=self.push_freq_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Connection status
        ttk.Separator(frame).grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=8)
        status_text = "Disconnected"
        status_color = "gray"
        if client and client.is_connected():
            status_text = "Connected"
            status_color = "green"
        elif client and client._running:
            status_text = "Connecting..."
            status_color = "orange"
        self.status_label = ttk.Label(frame, text=f"Status: {status_text}", foreground=status_color)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=3)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 4532
        try:
            poll = float(self.poll_var.get())
            if poll < 0.5:
                poll = 0.5
        except ValueError:
            poll = 2.0
        self.config.enabled = self.enabled_var.get()
        self.config.host = self.host_var.get().strip() or "127.0.0.1"
        self.config.port = port
        self.config.poll_interval = poll
        self.config.auto_band = self.auto_band_var.get()
        self.config.push_frequency = self.push_freq_var.get()
        self.on_save(self.config)
        self.win.destroy()
