"""
fldigi Two-Way Integration for FDLog Enhanced
Uses XML-RPC polling (default port 7362) to detect QSOs logged in fldigi
and optionally push frequency/callsign changes back to fldigi.
No external dependencies — uses Python's built-in xmlrpc.client.
"""

import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable

try:
    import xmlrpc.client
    XMLRPC_AVAILABLE = True
except ImportError:
    XMLRPC_AVAILABLE = False

from wsjtx_integration import freq_to_band, parse_exchange

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


@dataclass
class FldigiConfig:
    """Configuration for fldigi integration."""
    enabled: bool = False
    xmlrpc_host: str = "127.0.0.1"
    xmlrpc_port: int = 7362
    poll_interval: float = 1.5
    auto_log: bool = True
    auto_band: bool = True
    push_frequency: bool = True
    push_callsign: bool = False


class FldigiPoller:
    """fldigi integration controller. Polls via XML-RPC on a daemon thread."""

    _log_prefix = "fldigi"

    def __init__(self, config: FldigiConfig, on_qso_logged: Callable,
                 on_status_update: Callable, on_band_change: Optional[Callable] = None):
        self.config = config
        self.on_qso_logged = on_qso_logged
        self.on_status_update = on_status_update
        self.on_band_change = on_band_change
        self._proxy = None
        self._thread = None
        self._running = False
        self._connected = False
        self._current_freq = 0
        self._current_mode = ""
        self._current_band = None
        # QSO detection state
        self._last_call = ""
        self._cached_call = ""
        self._cached_freq = 0
        self._cached_exchange = ""

    def start(self):
        """Start the XML-RPC polling thread."""
        if self._running:
            return
        self._running = True
        url = f"http://{self.config.xmlrpc_host}:{self.config.xmlrpc_port}"
        try:
            self._proxy = xmlrpc.client.ServerProxy(url)
        except Exception as e:
            print(f"{self._log_prefix}: Failed to create XML-RPC proxy - {e}")
            self._running = False
            return
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"{self._log_prefix}: Polling {url}")

    def stop(self):
        """Stop the polling thread."""
        self._running = False
        self._proxy = None
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._connected = False
        self.on_status_update("Disconnected")
        print(f"{self._log_prefix}: Poller stopped")

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> dict:
        return {
            'connected': self._connected,
            'frequency': self._current_freq,
            'mode': self._current_mode,
            'running': self._running,
        }

    def _poll_loop(self):
        while self._running:
            try:
                # Test connection
                self._proxy.fldigi.name()
                if not self._connected:
                    self._connected = True
                    self.on_status_update("Connected")
                    print(f"{self._log_prefix}: Connected to fldigi")

                self._poll_status()
                self._poll_qso_fields()

            except Exception:
                if self._connected:
                    self._connected = False
                    self.on_status_update("Disconnected")
                    print(f"{self._log_prefix}: Connection lost")

            time.sleep(self.config.poll_interval)

    def _poll_status(self):
        """Read frequency and mode from fldigi, update status."""
        try:
            freq = int(self._proxy.main.get_frequency())
            mode = str(self._proxy.modem.get_name())
            self._current_freq = freq
            self._current_mode = mode

            band = freq_to_band(freq)
            if band and self._connected:
                self.on_status_update(f"Connected ({band[:-1]}m {mode})")

            # Auto-band-change detection
            if self.config.auto_band and band and band != self._current_band:
                self._current_band = band
                if self.on_band_change:
                    self.on_band_change(band)
        except Exception:
            pass

    def _poll_qso_fields(self):
        """Detect QSO logging by watching call field transitions."""
        try:
            call = str(self._proxy.log.get_call()).strip().upper()
            freq = int(self._proxy.main.get_frequency())
            exchange = str(self._proxy.log.get_exchange(1)).strip()
        except Exception:
            return

        if call:
            # Call is populated — cache current values
            self._cached_call = call
            self._cached_freq = freq
            self._cached_exchange = exchange
        elif self._last_call and not call:
            # Call just went from non-empty to empty — QSO was logged
            if self._cached_call and self.config.auto_log:
                self._process_qso()

        self._last_call = call

    def _process_qso(self):
        """Process a detected QSO from cached fields."""
        call = self._cached_call
        if not call:
            return

        band_mode = freq_to_band(self._cached_freq)
        if not band_mode:
            print(f"{self._log_prefix}: Unknown frequency {self._cached_freq} Hz, cannot determine band")
            self._cached_call = ""
            return

        exchange = self._cached_exchange
        parsed = parse_exchange(exchange)
        if parsed:
            fd_class, fd_section = parsed
            report = f"{fd_class.lower()} {fd_section.lower()}"
        else:
            report = exchange.lower() if exchange else ""
            if call:
                print(f"{self._log_prefix}: Could not parse exchange '{exchange}' for {call}")

        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%H%M")

        print(f"{self._log_prefix}: QSO logged - {call} on {band_mode}, exchange: {report}")
        self.on_qso_logged(call, band_mode, report, timestamp)

        # Clear cached values
        self._cached_call = ""
        self._cached_freq = 0
        self._cached_exchange = ""

    def set_frequency(self, freq_hz):
        """Push frequency to fldigi (two-way)."""
        if not self._connected or not self._proxy:
            return
        try:
            self._proxy.main.set_frequency(float(freq_hz))
            print(f"{self._log_prefix}: Set frequency to {freq_hz} Hz")
        except Exception as e:
            print(f"{self._log_prefix}: Failed to set frequency - {e}")

    def set_callsign(self, call):
        """Push callsign to fldigi (two-way, optional)."""
        if not self._connected or not self._proxy:
            return
        try:
            self._proxy.log.set_call(call)
            print(f"{self._log_prefix}: Set callsign to {call}")
        except Exception as e:
            print(f"{self._log_prefix}: Failed to set callsign - {e}")


# --- Settings Dialog ---

try:
    import tkinter as tk
    from tkinter import ttk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class FldigiSettingsDialog:
    """Tkinter dialog for fldigi integration settings."""

    def __init__(self, parent, config: FldigiConfig, poller: Optional[FldigiPoller], on_save: Callable):
        if not _TK_AVAILABLE:
            return
        self.config = config
        self.poller = poller
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("fldigi Integration Settings")
        self.win.geometry("400x400")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Enable/disable
        self.enabled_var = tk.BooleanVar(value=config.enabled)
        ttk.Checkbutton(frame, text="Enable fldigi Integration", variable=self.enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # XML-RPC Host
        ttk.Label(frame, text="XML-RPC Host:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.host_var = tk.StringVar(value=config.xmlrpc_host)
        ttk.Entry(frame, textvariable=self.host_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=3)

        # XML-RPC Port
        ttk.Label(frame, text="XML-RPC Port:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value=str(config.xmlrpc_port))
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=3)

        # Poll interval
        ttk.Label(frame, text="Poll Interval (s):").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.poll_var = tk.StringVar(value=str(config.poll_interval))
        ttk.Entry(frame, textvariable=self.poll_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=3)

        # Auto-log
        self.auto_log_var = tk.BooleanVar(value=config.auto_log)
        ttk.Checkbutton(frame, text="Auto-log QSOs from fldigi", variable=self.auto_log_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Auto-band
        self.auto_band_var = tk.BooleanVar(value=config.auto_band)
        ttk.Checkbutton(frame, text="Auto-switch band to match fldigi", variable=self.auto_band_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Push frequency
        self.push_freq_var = tk.BooleanVar(value=config.push_frequency)
        ttk.Checkbutton(frame, text="Push frequency changes to fldigi", variable=self.push_freq_var).grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Push callsign
        self.push_call_var = tk.BooleanVar(value=config.push_callsign)
        ttk.Checkbutton(frame, text="Push callsign to fldigi", variable=self.push_call_var).grid(
            row=7, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Connection status
        ttk.Separator(frame).grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=8)
        status_text = "Disconnected"
        status_color = "gray"
        if poller and poller.is_connected():
            status_text = "Connected"
            status_color = "green"
        elif poller and poller._running:
            status_text = "Polling..."
            status_color = "orange"
        self.status_label = ttk.Label(frame, text=f"Status: {status_text}", foreground=status_color)
        self.status_label.grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=3)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 7362
        try:
            poll = float(self.poll_var.get())
            if poll < 0.5:
                poll = 0.5
        except ValueError:
            poll = 1.5
        self.config.enabled = self.enabled_var.get()
        self.config.xmlrpc_host = self.host_var.get().strip() or "127.0.0.1"
        self.config.xmlrpc_port = port
        self.config.poll_interval = poll
        self.config.auto_log = self.auto_log_var.get()
        self.config.auto_band = self.auto_band_var.get()
        self.config.push_frequency = self.push_freq_var.get()
        self.config.push_callsign = self.push_call_var.get()
        self.on_save(self.config)
        self.win.destroy()
