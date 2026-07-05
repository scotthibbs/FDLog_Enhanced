"""
N1MM+ Logger Integration for FDLog Enhanced
One-way integration: QSOs logged by N1MM+ stations automatically appear in FDLog.
Listens for N1MM+'s "External UDP Broadcasts" (contactinfo/contactreplace/contactdelete/
RadioInfo XML messages, default port 12060). No external dependencies - uses the
standard library's xml.etree.ElementTree.

Enables mixed-mode Field Day club setups where some stations run N1MM+ and others
run FDLog Enhanced, with QSOs from both aggregated into one shared log.
"""

import socket
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Callable, Dict

from wsjtx_integration import freq_to_band
from n3fjp_integration import MODE_MAP


@dataclass
class N1MMConfig:
    """Configuration for N1MM+ integration."""
    enabled: bool = False
    udp_ip: str = "0.0.0.0"
    udp_port: int = 12060
    auto_log: bool = True
    auto_band: bool = True
    # N1MM+ stations networked together (sharing one contest DB) each broadcast
    # UDP messages for every contact in the shared log, not just their own -
    # IsOriginal distinguishes "logged here" from "relayed from a teammate".
    # Default True avoids double-logging the same QSO from multiple stations.
    only_original: bool = True


def _mode_suffix(mode_str: str) -> str:
    """Map an N1MM+ mode string (CW/USB/LSB/RTTY/FT8/...) to FDLog's band-mode suffix."""
    return MODE_MAP.get((mode_str or '').upper(), 'p')


def _extract_freq_hz(msg: Dict[str, str], keys=('txfreq', 'rxfreq')) -> int:
    """Pull a frequency in Hz out of an N1MM+ message dict.

    Prefers the tens-of-Hz numeric fields (txfreq/rxfreq, or freq for RadioInfo).
    Falls back to the locale-formatted 'band' field (MHz, comma or period decimal).
    """
    for key in keys:
        v = msg.get(key)
        if v:
            try:
                tenths = float(v)
                if tenths:
                    return int(tenths) * 10
            except ValueError:
                pass
    band_str = msg.get('band')
    if band_str:
        try:
            mhz = float(band_str.replace(',', '.'))
            if mhz:
                return int(mhz * 1_000_000)
        except ValueError:
            pass
    return 0


def n1mm_freq_to_band_mode(freq_hz: int, mode_str: str) -> Optional[str]:
    """Combine N1MM+'s actual mode with the verified band-edge table in
    wsjtx_integration (that table hardcodes a 'd' suffix, since it's only ever
    used for digital-mode apps - strip it and substitute the real suffix)."""
    if not freq_hz:
        return None
    raw = freq_to_band(freq_hz)
    if not raw:
        return None
    return raw[:-1] + _mode_suffix(mode_str)


def build_report(exchange1: str, section: str) -> str:
    """N1MM+ already splits the FD exchange into separate class/section fields."""
    exchange1 = (exchange1 or '').strip()
    section = (section or '').strip()
    combined = f"{exchange1} {section}".strip()
    return combined.lower()


def parse_message(data: bytes) -> Optional[Dict[str, str]]:
    """Parse one N1MM+ UDP datagram into a dict with a '_type' key (lowercased
    root tag: contactinfo/contactreplace/contactdelete/radioinfo/...) plus one
    lowercased key per child element."""
    try:
        text = data.decode('utf-8', errors='replace').strip()
        if not text.startswith('<'):
            return None
        root = ET.fromstring(text)
    except Exception:
        return None
    msg: Dict[str, str] = {'_type': root.tag.lower()}
    for child in root:
        msg[child.tag.lower()] = (child.text or '').strip()
    return msg


class N1MMListener:
    """Main N1MM+ integration controller. Listens for UDP packets on a daemon thread."""

    _log_prefix = "N1MM+"
    ACTIVITY_TIMEOUT = 30.0  # seconds without any message = disconnected

    def __init__(self, config: N1MMConfig, on_qso_logged: Callable, on_status_update: Callable,
                 on_band_change: Optional[Callable] = None,
                 on_qso_deleted: Optional[Callable] = None,
                 on_qso_replaced: Optional[Callable] = None):
        self.config = config
        self.on_qso_logged = on_qso_logged
        self.on_status_update = on_status_update
        self.on_band_change = on_band_change
        self.on_qso_deleted = on_qso_deleted
        self.on_qso_replaced = on_qso_replaced
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._last_activity = 0.0
        self._current_band: Optional[str] = None

    def start(self):
        if self._running:
            return
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.config.udp_ip, self.config.udp_port))
            self._sock.settimeout(2.0)
        except OSError as e:
            print(f"{self._log_prefix}: Failed to bind UDP {self.config.udp_ip}:{self.config.udp_port} - {e}")
            self._running = False
            return
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"{self._log_prefix}: Listening on {self.config.udp_ip}:{self.config.udp_port}")

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._connected = False
        self.on_status_update("Disconnected")
        print(f"{self._log_prefix}: Listener stopped")

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> dict:
        return {
            'connected': self._connected,
            'band': self._current_band,
            'running': self._running,
        }

    def _listen_loop(self):
        while self._running:
            if self._connected and (time.time() - self._last_activity > self.ACTIVITY_TIMEOUT):
                self._connected = False
                self.on_status_update("Disconnected")
                print(f"{self._log_prefix}: Connection lost (no traffic)")

            try:
                data, addr = self._sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    print(f"{self._log_prefix}: Socket error in listener")
                break

            msg = parse_message(data)
            if msg is None:
                continue

            was_connected = self._connected
            self._connected = True
            self._last_activity = time.time()
            if not was_connected:
                self.on_status_update("Connected")
                print(f"{self._log_prefix}: Connected - traffic from {addr[0]}")

            try:
                self._handle_message(msg)
            except Exception as e:
                print(f"{self._log_prefix}: Error handling message - {e}")

    def _handle_message(self, msg: Dict[str, str]):
        mtype = msg.get('_type', '')
        if mtype == 'radioinfo':
            self._handle_radioinfo(msg)
        elif mtype == 'contactinfo':
            self._handle_contact(msg)
        elif mtype == 'contactreplace':
            if self.on_qso_replaced:
                call = msg.get('call', '').strip().upper()
                print(f"{self._log_prefix}: QSO replaced - {call}")
                self.on_qso_replaced(call, msg)
            else:
                self._handle_contact(msg)
        elif mtype == 'contactdelete':
            call = (msg.get('call', '') or msg.get('oldcall', '')).strip().upper()
            print(f"{self._log_prefix}: QSO deleted - {call}")
            if self.on_qso_deleted:
                self.on_qso_deleted(call, msg)

    def _handle_radioinfo(self, msg: Dict[str, str]):
        freq_hz = _extract_freq_hz(msg, keys=('txfreq', 'freq'))
        mode_str = msg.get('mode', '')
        band_mode = n1mm_freq_to_band_mode(freq_hz, mode_str)
        if band_mode and band_mode != self._current_band:
            self._current_band = band_mode
            if self.config.auto_band and self.on_band_change:
                self.on_band_change(band_mode)
            self.on_status_update(f"Connected ({band_mode[:-1]}m {mode_str})")

    def _handle_contact(self, msg: Dict[str, str]):
        if not self.config.auto_log:
            return
        call = msg.get('call', '').strip().upper()
        if not call:
            print(f"{self._log_prefix}: Ignoring QSO with empty callsign")
            return

        is_original = msg.get('isoriginal', 'true').strip().lower() != 'false'
        if self.config.only_original and not is_original:
            print(f"{self._log_prefix}: Skipping relayed contact for {call} (not original)")
            return

        freq_hz = _extract_freq_hz(msg)
        mode_str = msg.get('mode', '')
        band_mode = n1mm_freq_to_band_mode(freq_hz, mode_str)
        if not band_mode:
            print(f"{self._log_prefix}: Unknown frequency for {call}, cannot determine band")
            return

        report = build_report(msg.get('exchange1', ''), msg.get('section', ''))
        print(f"{self._log_prefix}: QSO logged - {call} on {band_mode}, exchange: {report}")
        # Timestamp intentionally not passed through - FDLog uses its own now()
        # for consistency, same as the N3FJP integration.
        self.on_qso_logged(call, band_mode, report, None)


# --- Settings Dialog ---

try:
    import tkinter as tk
    from tkinter import ttk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class N1MMSettingsDialog:
    """Tkinter dialog for N1MM+ integration settings."""

    def __init__(self, parent, config: N1MMConfig, listener: Optional[N1MMListener], on_save: Callable):
        if not _TK_AVAILABLE:
            return
        self.config = config
        self.listener = listener
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("N1MM+ Integration Settings")
        self.win.geometry("420x360")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.enabled_var = tk.BooleanVar(value=config.enabled)
        ttk.Checkbutton(frame, text="Enable N1MM+ Integration", variable=self.enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(frame, text="UDP Listen IP:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.ip_var = tk.StringVar(value=config.udp_ip)
        ttk.Entry(frame, textvariable=self.ip_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=3)

        ttk.Label(frame, text="UDP Port:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value=str(config.udp_port))
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=3)

        self.auto_log_var = tk.BooleanVar(value=config.auto_log)
        ttk.Checkbutton(frame, text="Auto-log QSOs from N1MM+", variable=self.auto_log_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.auto_band_var = tk.BooleanVar(value=config.auto_band)
        ttk.Checkbutton(frame, text="Auto-switch band to match N1MM+", variable=self.auto_band_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.only_original_var = tk.BooleanVar(value=config.only_original)
        ttk.Checkbutton(frame, text="Only log original contacts (skip teammate relays)",
                        variable=self.only_original_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Separator(frame).grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=8)
        status_text = "Disconnected"
        status_color = "gray"
        if listener and listener.is_connected():
            status_text = "Connected"
            status_color = "green"
        elif listener and listener._running:
            status_text = "Listening..."
            status_color = "orange"
        self.status_label = ttk.Label(frame, text=f"Status: {status_text}", foreground=status_color)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 12060
        self.config.enabled = self.enabled_var.get()
        self.config.udp_ip = self.ip_var.get().strip() or "0.0.0.0"
        self.config.udp_port = port
        self.config.auto_log = self.auto_log_var.get()
        self.config.auto_band = self.auto_band_var.get()
        self.config.only_original = self.only_original_var.get()
        self.on_save(self.config)
        self.win.destroy()
