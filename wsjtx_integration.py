"""
WSJT-X Integration for FDLog Enhanced
One-way integration: QSOs logged in WSJT-X automatically appear in FDLog.
Implements Qt QDataStream binary protocol parsing with no external dependencies.
"""

import struct
import socket
import threading
import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable

# Frequency-to-band mapping (Hz ranges to FDLog band+mode string)
FREQ_BAND_MAP = [
    (1800000, 2000000, "160d"),
    (3500000, 4000000, "80d"),
    (7000000, 7300000, "40d"),
    (14000000, 14350000, "20d"),
    (21000000, 21450000, "15d"),
    (28000000, 29700000, "10d"),
    (50000000, 54000000, "6d"),
    (144000000, 148000000, "2d"),
    (420000000, 450000000, "220d"),
]


def freq_to_band(freq_hz):
    """Convert frequency in Hz to FDLog band+mode string."""
    for lo, hi, band in FREQ_BAND_MAP:
        if lo <= freq_hz <= hi:
            return band
    return None


# Exchange parsing regex: class (digits + letter A-F) and section
EXCHANGE_RE = re.compile(r'(\d+[A-Fa-f])\s+([A-Za-z]{2,3})')


def parse_exchange(exchange_str):
    """Parse Field Day exchange string into (class, section) or None."""
    if not exchange_str:
        return None
    m = EXCHANGE_RE.search(exchange_str)
    if m:
        return m.group(1).upper(), m.group(2).upper()
    return None


@dataclass
class WSJTXConfig:
    """Configuration for WSJT-X integration."""
    enabled: bool = False
    udp_port: int = 2237
    udp_ip: str = "127.0.0.1"
    auto_log: bool = True
    auto_band: bool = True


class QDataStreamParser:
    """Parse Qt QDataStream binary format from a bytes buffer."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def _read(self, n):
        if self.pos + n > len(self.data):
            raise ValueError(f"Buffer underrun: need {n} bytes at pos {self.pos}, have {len(self.data)}")
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result

    def read_quint32(self) -> int:
        return struct.unpack('>I', self._read(4))[0]

    def read_qint32(self) -> int:
        return struct.unpack('>i', self._read(4))[0]

    def read_quint64(self) -> int:
        return struct.unpack('>Q', self._read(8))[0]

    def read_double(self) -> float:
        return struct.unpack('>d', self._read(8))[0]

    def read_bool(self) -> bool:
        return struct.unpack('>?', self._read(1))[0]

    def read_quint8(self) -> int:
        return struct.unpack('>B', self._read(1))[0]

    def read_utf8(self) -> str:
        """Read a Qt UTF-8 string (4-byte length prefix, then bytes). Length 0xFFFFFFFF means null."""
        length = self.read_quint32()
        if length == 0xFFFFFFFF:
            return ""
        return self._read(length).decode('utf-8', errors='replace')

    def read_qdatetime(self) -> Optional[datetime]:
        """Read a Qt QDateTime: julian day (qint64), ms since midnight (quint32), timespec (quint8)."""
        julian_day = struct.unpack('>q', self._read(8))[0]
        ms_since_midnight = self.read_quint32()
        timespec = self.read_quint8()
        if julian_day <= 0:
            return None
        # Convert Julian day to date
        # Julian day 2440588 = 1970-01-01
        days_since_epoch = julian_day - 2440588
        try:
            ts = days_since_epoch * 86400 + ms_since_midnight / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    def remaining(self) -> int:
        return len(self.data) - self.pos


# --- Message classes ---

class WSJTXMessage:
    """Base class for WSJT-X network messages."""
    msg_type: int = -1
    client_id: str = ""

    @staticmethod
    def parse(data: bytes) -> Optional['WSJTXMessage']:
        """Factory: parse raw UDP datagram into a message object."""
        p = QDataStreamParser(data)
        try:
            magic = p.read_quint32()
            if magic != 0xADBCCBDA:
                return None
            schema = p.read_quint32()  # schema version
            msg_type = p.read_quint32()
            client_id = p.read_utf8()
        except (ValueError, struct.error):
            return None

        parsers = {
            0: HeartbeatMessage._parse,
            1: StatusMessage._parse,
            2: DecodeMessage._parse,
            5: QSOLoggedMessage._parse,
            6: CloseMessage._parse,
            12: LoggedADIFMessage._parse,
        }

        parser = parsers.get(msg_type)
        if parser is None:
            return None
        try:
            return parser(p, client_id)
        except (ValueError, struct.error):
            return None


class HeartbeatMessage(WSJTXMessage):
    msg_type = 0

    def __init__(self, client_id, max_schema, version, revision):
        self.client_id = client_id
        self.max_schema = max_schema
        self.version = version
        self.revision = revision

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        max_schema = p.read_quint32()
        version = p.read_utf8()
        revision = p.read_utf8()
        return HeartbeatMessage(client_id, max_schema, version, revision)


class StatusMessage(WSJTXMessage):
    msg_type = 1

    def __init__(self, client_id, dial_freq, mode, dx_call, report, tx_mode,
                 tx_enabled, transmitting, decoding, rx_df, tx_df, de_call,
                 de_grid, dx_grid, tx_watchdog, sub_mode, fast_mode,
                 special_op, freq_tolerance, tr_period, config_name, tx_message):
        self.client_id = client_id
        self.dial_freq = dial_freq
        self.mode = mode
        self.dx_call = dx_call
        self.report = report
        self.tx_mode = tx_mode
        self.tx_enabled = tx_enabled
        self.transmitting = transmitting
        self.decoding = decoding
        self.rx_df = rx_df
        self.tx_df = tx_df
        self.de_call = de_call
        self.de_grid = de_grid
        self.dx_grid = dx_grid
        self.tx_watchdog = tx_watchdog
        self.sub_mode = sub_mode
        self.fast_mode = fast_mode
        self.special_op = special_op
        self.freq_tolerance = freq_tolerance
        self.tr_period = tr_period
        self.config_name = config_name
        self.tx_message = tx_message

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        dial_freq = p.read_quint64()
        mode = p.read_utf8()
        dx_call = p.read_utf8()
        report = p.read_utf8()
        tx_mode = p.read_utf8()
        tx_enabled = p.read_bool()
        transmitting = p.read_bool()
        decoding = p.read_bool()
        rx_df = p.read_quint32()
        tx_df = p.read_quint32()
        de_call = p.read_utf8()
        de_grid = p.read_utf8()
        dx_grid = p.read_utf8()
        tx_watchdog = p.read_bool()
        sub_mode = p.read_utf8()
        fast_mode = p.read_bool()
        special_op = p.read_quint8()
        freq_tolerance = p.read_quint32()
        tr_period = p.read_quint32()
        config_name = p.read_utf8()
        tx_message = p.read_utf8() if p.remaining() > 0 else ""
        return StatusMessage(client_id, dial_freq, mode, dx_call, report, tx_mode,
                             tx_enabled, transmitting, decoding, rx_df, tx_df, de_call,
                             de_grid, dx_grid, tx_watchdog, sub_mode, fast_mode,
                             special_op, freq_tolerance, tr_period, config_name, tx_message)


class DecodeMessage(WSJTXMessage):
    msg_type = 2

    def __init__(self, client_id, is_new, time_ms, snr, delta_time, delta_freq, mode, message, low_confidence, off_air):
        self.client_id = client_id
        self.is_new = is_new
        self.time_ms = time_ms
        self.snr = snr
        self.delta_time = delta_time
        self.delta_freq = delta_freq
        self.mode = mode
        self.message = message
        self.low_confidence = low_confidence
        self.off_air = off_air

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        is_new = p.read_bool()
        time_ms = p.read_quint32()
        snr = p.read_qint32()
        delta_time = p.read_double()
        delta_freq = p.read_quint32()
        mode = p.read_utf8()
        message = p.read_utf8()
        low_confidence = p.read_bool()
        off_air = p.read_bool() if p.remaining() > 0 else False
        return DecodeMessage(client_id, is_new, time_ms, snr, delta_time, delta_freq, mode, message, low_confidence, off_air)


class QSOLoggedMessage(WSJTXMessage):
    msg_type = 5

    def __init__(self, client_id, date_time_off, dx_call, dx_grid, tx_freq,
                 mode, report_sent, report_recv, tx_power, comments,
                 name, date_time_on, operator_call, my_call, my_grid,
                 exchange_sent, exchange_recv):
        self.client_id = client_id
        self.date_time_off = date_time_off
        self.dx_call = dx_call
        self.dx_grid = dx_grid
        self.tx_freq = tx_freq
        self.mode = mode
        self.report_sent = report_sent
        self.report_recv = report_recv
        self.tx_power = tx_power
        self.comments = comments
        self.name = name
        self.date_time_on = date_time_on
        self.operator_call = operator_call
        self.my_call = my_call
        self.my_grid = my_grid
        self.exchange_sent = exchange_sent
        self.exchange_recv = exchange_recv

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        date_time_off = p.read_qdatetime()
        dx_call = p.read_utf8()
        dx_grid = p.read_utf8()
        tx_freq = p.read_quint64()
        mode = p.read_utf8()
        report_sent = p.read_utf8()
        report_recv = p.read_utf8()
        tx_power = p.read_utf8()
        comments = p.read_utf8()
        name = p.read_utf8()
        date_time_on = p.read_qdatetime()
        operator_call = p.read_utf8()
        my_call = p.read_utf8()
        my_grid = p.read_utf8()
        exchange_sent = p.read_utf8() if p.remaining() > 0 else ""
        exchange_recv = p.read_utf8() if p.remaining() > 0 else ""
        return QSOLoggedMessage(client_id, date_time_off, dx_call, dx_grid, tx_freq,
                                mode, report_sent, report_recv, tx_power, comments,
                                name, date_time_on, operator_call, my_call, my_grid,
                                exchange_sent, exchange_recv)


class CloseMessage(WSJTXMessage):
    msg_type = 6

    def __init__(self, client_id):
        self.client_id = client_id

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        return CloseMessage(client_id)


class LoggedADIFMessage(WSJTXMessage):
    msg_type = 12

    def __init__(self, client_id, adif_text):
        self.client_id = client_id
        self.adif_text = adif_text

    @staticmethod
    def _parse(p: QDataStreamParser, client_id: str):
        adif_text = p.read_utf8()
        return LoggedADIFMessage(client_id, adif_text)


# --- Listener ---

class WSJTXListener:
    """Main WSJT-X integration controller. Listens for UDP packets on a daemon thread."""

    HEARTBEAT_TIMEOUT = 15.0  # seconds without heartbeat = disconnected

    def __init__(self, config: WSJTXConfig, on_qso_logged: Callable, on_status_update: Callable):
        self.config = config
        self.on_qso_logged = on_qso_logged
        self.on_status_update = on_status_update
        self._sock = None
        self._thread = None
        self._running = False
        self._connected = False
        self._last_heartbeat = 0.0
        self._current_freq = 0
        self._current_mode = ""
        self._client_id = ""

    def start(self):
        """Start the UDP listener thread."""
        if self._running:
            return
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.config.udp_ip, self.config.udp_port))
            self._sock.settimeout(2.0)
        except OSError as e:
            print(f"WSJT-X: Failed to bind UDP {self.config.udp_ip}:{self.config.udp_port} - {e}")
            self._running = False
            return
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"WSJT-X: Listening on {self.config.udp_ip}:{self.config.udp_port}")

    def stop(self):
        """Stop the UDP listener."""
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
        print("WSJT-X: Listener stopped")

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> dict:
        return {
            'connected': self._connected,
            'client_id': self._client_id,
            'frequency': self._current_freq,
            'mode': self._current_mode,
            'running': self._running,
        }

    def _listen_loop(self):
        while self._running:
            # Check heartbeat timeout
            if self._connected and (time.time() - self._last_heartbeat > self.HEARTBEAT_TIMEOUT):
                self._connected = False
                self.on_status_update("Disconnected")
                print("WSJT-X: Connection lost (heartbeat timeout)")

            try:
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    print("WSJT-X: Socket error in listener")
                break

            msg = WSJTXMessage.parse(data)
            if msg is None:
                continue

            self._handle_message(msg)

    def _handle_message(self, msg):
        if isinstance(msg, HeartbeatMessage):
            was_connected = self._connected
            self._connected = True
            self._last_heartbeat = time.time()
            self._client_id = msg.client_id
            if not was_connected:
                self.on_status_update("Connected")
                print(f"WSJT-X: Connected - {msg.version} ({msg.client_id})")

        elif isinstance(msg, StatusMessage):
            self._current_freq = msg.dial_freq
            self._current_mode = msg.mode
            band = freq_to_band(msg.dial_freq)
            if band and self._connected:
                self.on_status_update(f"Connected ({band[:-1]}m {msg.mode})")

        elif isinstance(msg, QSOLoggedMessage):
            if self.config.auto_log:
                self._process_qso(msg)

        elif isinstance(msg, CloseMessage):
            self._connected = False
            self.on_status_update("Disconnected")
            print(f"WSJT-X: Client closed ({msg.client_id})")

    def _process_qso(self, msg: QSOLoggedMessage):
        """Process a logged QSO from WSJT-X."""
        call = msg.dx_call.strip().upper()
        if not call:
            print("WSJT-X: Ignoring QSO with empty callsign")
            return

        # Determine band
        band_mode = freq_to_band(msg.tx_freq)
        if not band_mode:
            print(f"WSJT-X: Unknown frequency {msg.tx_freq} Hz, cannot determine band")
            return

        # Parse exchange
        exchange = msg.exchange_recv.strip()
        if not exchange:
            # Try comments field as fallback
            exchange = msg.comments.strip()

        parsed = parse_exchange(exchange)
        if parsed:
            fd_class, fd_section = parsed
            report = f"{fd_class.lower()} {fd_section.lower()}"
        else:
            # Use raw exchange if we can't parse it
            report = exchange.lower() if exchange else ""
            print(f"WSJT-X: Could not parse exchange '{exchange}' for {call}")

        # Determine timestamp
        if msg.date_time_off:
            timestamp = msg.date_time_off.strftime("%H%M")
        else:
            timestamp = datetime.now(timezone.utc).strftime("%H%M")

        print(f"WSJT-X: QSO logged - {call} on {band_mode}, exchange: {report}")
        self.on_qso_logged(call, band_mode, report, timestamp)


# --- Settings Dialog ---

try:
    import tkinter as tk
    from tkinter import ttk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class WSJTXSettingsDialog:
    """Tkinter dialog for WSJT-X integration settings."""

    def __init__(self, parent, config: WSJTXConfig, listener: Optional[WSJTXListener], on_save: Callable):
        if not _TK_AVAILABLE:
            return
        self.config = config
        self.listener = listener
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("WSJT-X Integration Settings")
        self.win.geometry("400x320")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Enable/disable
        self.enabled_var = tk.BooleanVar(value=config.enabled)
        ttk.Checkbutton(frame, text="Enable WSJT-X Integration", variable=self.enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # UDP IP
        ttk.Label(frame, text="UDP Listen IP:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.ip_var = tk.StringVar(value=config.udp_ip)
        ttk.Entry(frame, textvariable=self.ip_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=3)

        # UDP Port
        ttk.Label(frame, text="UDP Port:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value=str(config.udp_port))
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=3)

        # Auto-log
        self.auto_log_var = tk.BooleanVar(value=config.auto_log)
        ttk.Checkbutton(frame, text="Auto-log QSOs from WSJT-X", variable=self.auto_log_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Auto-band
        self.auto_band_var = tk.BooleanVar(value=config.auto_band)
        ttk.Checkbutton(frame, text="Auto-switch band to match WSJT-X", variable=self.auto_band_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Connection status
        ttk.Separator(frame).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=8)
        status_text = "Disconnected"
        status_color = "gray"
        if listener and listener.is_connected():
            status_text = "Connected"
            status_color = "green"
        elif listener and listener._running:
            status_text = "Listening..."
            status_color = "orange"
        self.status_label = ttk.Label(frame, text=f"Status: {status_text}", foreground=status_color)
        self.status_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=3)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 2237
        self.config.enabled = self.enabled_var.get()
        self.config.udp_ip = self.ip_var.get().strip() or "127.0.0.1"
        self.config.udp_port = port
        self.config.auto_log = self.auto_log_var.get()
        self.config.auto_band = self.auto_band_var.get()
        self.on_save(self.config)
        self.win.destroy()
