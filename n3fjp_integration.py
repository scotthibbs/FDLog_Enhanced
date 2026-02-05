"""
N3FJP API Integration for FDLog Enhanced
TCP client (connect to N3FJP server) and TCP server (accept N3FJP-compatible clients).
Uses XML-style <CMD>...</CMD> messages over TCP, default port 1100.
No external dependencies — uses Python's built-in socket and threading.
"""

import re
import socket
import socketserver
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable, List, Dict

from wsjtx_integration import freq_to_band, parse_exchange

# Reverse mapping: FDLog band string → default frequency in Hz
BAND_FREQ_MAP = {
    "160d": 1840000, "160c": 1840000, "160p": 1900000,
    "80d": 3573000, "80c": 3550000, "80p": 3900000,
    "40d": 7074000, "40c": 7050000, "40p": 7250000,
    "20d": 14074000, "20c": 14050000, "20p": 14250000,
    "15d": 21074000, "15c": 21050000, "15p": 21350000,
    "10d": 28074000, "10c": 28050000, "10p": 28400000,
    "6d": 50313000, "6c": 50100000, "6p": 50150000,
    "2d": 144174000, "2c": 144100000, "2p": 144200000,
    "220d": 432065000, "220c": 432100000, "220p": 432100000,
}

# Frequency → band mode suffix based on frequency ranges
# Maps N3FJP mode strings to FDLog mode suffixes
MODE_MAP = {
    "CW": "c", "SSB": "p", "USB": "p", "LSB": "p", "AM": "p", "FM": "p",
    "PH": "p",  # N3FJP uses "PH" for phone
    "RTTY": "d", "PSK31": "d", "PSK": "d", "FT8": "d", "FT4": "d",
    "JS8": "d", "MFSK": "d", "OLIVIA": "d", "JT65": "d", "JT9": "d",
    "DIGI": "d", "DIG": "d", "DATA": "d", "DG": "d",  # N3FJP uses "DIG"/"DG" for digital
}


@dataclass
class N3FJPConfig:
    """Configuration for N3FJP integration."""
    client_enabled: bool = False
    server_enabled: bool = False
    host: str = "127.0.0.1"
    client_port: int = 1100
    server_port: int = 1100
    auto_log: bool = True
    auto_band: bool = True


# ---------------------------------------------------------------------------
# Protocol helpers
# ---------------------------------------------------------------------------

_CMD_RE = re.compile(r'<CMD>(.*?)</CMD>', re.DOTALL)
_FIELD_RE = re.compile(r'<(\w+)>(.*?)</\1>', re.DOTALL)
_WRAPPER_RE = re.compile(r'^<(\w+)>(.*)', re.DOTALL)


def parse_messages(data: str) -> List[Dict[str, str]]:
    """Extract all <CMD>...</CMD> blocks, return list of dicts.

    Each dict has a '_type' key for the command name and additional keys
    for any sub-fields found within.

    Handles N3FJP API v2 wrapper-tag format:
      <CMD><ENTEREVENT><CALL>W1AW</CALL>...</ENTEREVENT></CMD>
    as well as bare-word format:
      <CMD>PROGRAM<PROGRAM>FDLog</PROGRAM></CMD>
    """
    results = []
    for m in _CMD_RE.finditer(data):
        inner = m.group(1).strip()
        msg: Dict[str, str] = {}

        if inner.startswith('<'):
            # Wrapper-tag format: <COMMANDTYPE><fields...></COMMANDTYPE>
            wm = _WRAPPER_RE.match(inner)
            if wm:
                cmd_type = wm.group(1).upper()
                msg['_type'] = cmd_type
                content = wm.group(2)
                # Strip closing wrapper tag if present
                close_tag = f'</{wm.group(1)}>'
                idx = content.upper().rfind(close_tag.upper())
                if idx >= 0:
                    content = content[:idx]
                # Extract sub-fields from the unwrapped content
                for fm in _FIELD_RE.finditer(content):
                    msg[fm.group(1).upper()] = fm.group(2)
            else:
                msg['_type'] = 'UNKNOWN'
        else:
            # Bare-word format: COMMAND <FIELD>value</FIELD>...
            for fm in _FIELD_RE.finditer(inner):
                msg[fm.group(1).upper()] = fm.group(2)
            if not msg:
                parts = inner.split(None, 1)
                msg['_type'] = parts[0].upper() if parts else inner.upper()
                if len(parts) > 1:
                    msg['_value'] = parts[1]
            else:
                prefix = inner[:inner.index('<')].strip() if '<' in inner else inner
                tokens = prefix.split()
                msg['_type'] = tokens[0].upper() if tokens else 'UNKNOWN'
        results.append(msg)
    return results


def build_cmd(command: str, **fields) -> str:
    """Build a <CMD>command <FIELD>value</FIELD>...</CMD>\\r\\n string."""
    parts = [command]
    for key, val in fields.items():
        parts.append(f"<{key}>{val}</{key}>")
    return f"<CMD>{''.join(parts)}</CMD>\r\n"


def build_cmd_wrapped(command: str, **fields) -> str:
    """Build N3FJP API v2 wrapped format:
    <CMD><COMMAND><FIELD>value</FIELD>...</COMMAND></CMD>\\r\\n
    """
    inner_parts = []
    for key, val in fields.items():
        inner_parts.append(f"<{key}>{val}</{key}>")
    return f"<CMD><{command}>{''.join(inner_parts)}</{command}></CMD>\r\n"


def parse_adif(adif_str: str) -> Dict[str, str]:
    """Parse a minimal ADIF record into a dict of field→value."""
    result = {}
    for m in re.finditer(r'<(\w+):\d+(?::\w+)?>([^<]*)', adif_str):
        result[m.group(1).upper()] = m.group(2).strip()
    return result


def _mode_suffix(mode_str: str) -> str:
    """Map a mode string to FDLog band-mode suffix (c/p/d)."""
    return MODE_MAP.get(mode_str.upper(), "p")


# ---------------------------------------------------------------------------
# N3FJP Client — connect to an N3FJP server
# ---------------------------------------------------------------------------

class N3FJPClient:
    """TCP client that connects to an N3FJP-compatible server."""

    _log_prefix = "N3FJP-Client"

    def __init__(self, config: N3FJPConfig, on_qso_logged: Callable,
                 on_status_update: Callable, on_band_change: Optional[Callable] = None):
        self.config = config
        self.on_qso_logged = on_qso_logged
        self.on_status_update = on_status_update
        self.on_band_change = on_band_change
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._current_band = None
        self._buffer = ""

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._connected = False
        self.on_status_update("Disconnected")
        print(f"{self._log_prefix}: Stopped")

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> dict:
        return {
            'connected': self._connected,
            'running': self._running,
        }

    def set_frequency(self, freq_hz: int):
        """Send CHANGEFREQ to the N3FJP server."""
        if self._connected and self._sock:
            self._send(build_cmd_wrapped("CHANGEFREQ", VALUE=str(freq_hz)))

    def push_callsign(self, call: str):
        """Send UPDATE with callsign to the N3FJP server."""
        if self._connected and self._sock:
            self._send(build_cmd_wrapped("UPDATE", CONTROL="TXTENTRYCALL", VALUE=call))

    def _send(self, msg: str):
        try:
            self._sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"{self._log_prefix}: Send error - {e}")

    def _run_loop(self):
        backoff = 1
        while self._running:
            try:
                self._connect()
                backoff = 1
                self._receive_loop()
            except Exception as e:
                if self._running:
                    print(f"{self._log_prefix}: Connection error - {e}")
            if self._connected:
                self._connected = False
                self.on_status_update("Disconnected")
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
            if self._running:
                time.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 30)

    def _connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(10)
        self._sock.connect((self.config.host, self.config.client_port))
        self._sock.settimeout(1)
        self._connected = True
        self._buffer = ""
        self.on_status_update("Connected")
        print(f"{self._log_prefix}: Connected to {self.config.host}:{self.config.client_port}")
        # Identify ourselves — N3FJP expects fields directly inside <CMD>
        self._send("<CMD><PROGRAM>FDLog Enhanced</PROGRAM><APIVERSION>1.0.0.0</APIVERSION></CMD>\r\n")
        # Request update notifications — N3FJP API v2 wrapped format
        self._send(build_cmd_wrapped("SETUPDATESTATE", VALUE="TRUE"))

    def _receive_loop(self):
        while self._running and self._connected:
            try:
                data = self._sock.recv(4096)
                if not data:
                    print(f"{self._log_prefix}: Server closed connection")
                    return
                self._buffer += data.decode('utf-8', errors='replace')
                self._process_buffer()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"{self._log_prefix}: Receive error - {e}")
                return

    def _process_buffer(self):
        messages = parse_messages(self._buffer)
        # Remove processed content up to the last </CMD>
        last_end = self._buffer.rfind('</CMD>')
        if last_end >= 0:
            self._buffer = self._buffer[last_end + 6:]
        for msg in messages:
            self._handle_message(msg)

    def _handle_message(self, msg: Dict[str, str]):
        cmd = msg.get('_type', '')
        if cmd == 'ENTEREVENT':
            self._handle_enter_event(msg)
        elif cmd == 'CONTACTREPLACE':
            # N3FJP v2 alternate name for a logged QSO
            self._handle_enter_event(msg)
        elif cmd == 'READBMFRESPONSE':
            self._handle_band_change(msg)
        elif cmd == 'UPDATE':
            self._handle_update(msg)
        elif cmd == 'CALLTABEVENT':
            self._handle_calltab(msg)
        elif cmd == 'PROGRAMRESPONSE':
            ver = msg.get('VER', '?')
            apiver = msg.get('APIVER', '?')
            print(f"{self._log_prefix}: Server: N3FJP v{ver}, API v{apiver}")
        elif cmd == 'SETUPDATESTATERESPONSE':
            print(f"{self._log_prefix}: Update notifications enabled")
        elif cmd == 'CMD_NOT_FOUND':
            print(f"{self._log_prefix}: WARNING - Server did not recognize a command")

    def _handle_update(self, msg: Dict[str, str]):
        """Handle UPDATE notification — a field changed in N3FJP."""
        # Track frequency/band changes from UPDATE messages
        freq_str = msg.get('FREQ', msg.get('TXTENTRYFREQUENCY', '0'))
        try:
            freq_hz = int(float(freq_str))
        except ValueError:
            freq_hz = 0
        if freq_hz:
            band = freq_to_band(freq_hz)
            if band and band != self._current_band:
                self._current_band = band
                if self.config.auto_band and self.on_band_change:
                    self.on_band_change(band)
                self.on_status_update(f"Connected ({band[:-1]}m)")

    def _handle_calltab(self, msg: Dict[str, str]):
        """Handle CALLTABEVENT — user tabbed from call field in N3FJP."""
        freq_str = msg.get('FREQ', msg.get('TXTENTRYFREQUENCY', '0'))
        try:
            freq_hz = int(float(freq_str))
        except ValueError:
            freq_hz = 0
        band = freq_to_band(freq_hz) if freq_hz else None
        if not band:
            band_str = msg.get('BAND', '')
            mode_str = msg.get('MODE', msg.get('MODETEST', 'PH'))
            suffix = _mode_suffix(mode_str)
            if band_str:
                band = band_str.replace('m', '').replace('M', '').replace('cm', '') + suffix
        if band and band != self._current_band:
            self._current_band = band
            if self.config.auto_band and self.on_band_change:
                self.on_band_change(band)
            band_num = band[:-1]
            self.on_status_update(f"Connected ({band_num}m)")

    def _handle_enter_event(self, msg: Dict[str, str]):
        """Process an ENTEREVENT/CONTACTREPLACE — a QSO was logged in N3FJP."""
        # N3FJP uses various field names depending on version and contest type
        call = (msg.get('CALL', '') or msg.get('TXTENTRYCALL', '')).strip().upper()
        if not call:
            return
        freq_str = msg.get('FREQ', msg.get('TXTENTRYFREQUENCY', '0'))
        try:
            freq_hz = int(float(freq_str))
        except ValueError:
            freq_hz = 0
        mode = msg.get('MODE', msg.get('TXTENTRYMODE', msg.get('CBOENTRYMODE', 'SSB')))
        band_mode = freq_to_band(freq_hz) if freq_hz else None
        if not band_mode:
            # Try to construct from band/mode fields
            band_str = msg.get('BAND', msg.get('TXTENTRYBAND', msg.get('CBOENTRYBAND', '')))
            suffix = _mode_suffix(mode)
            if band_str:
                band_mode = band_str.replace('m', '').replace('M', '') + suffix
        if not band_mode:
            print(f"{self._log_prefix}: Cannot determine band for {call}")
            return
        # FD exchange: try direct exchange field first
        exchange = (msg.get('EXCHANGE', '') or msg.get('MODESENT', '') or
                    msg.get('TXTENTRYEXCHANGE', ''))
        # Combine class + section fields (N3FJP FD uses CLASS and ARRL_SECT)
        if not exchange:
            fd_class = msg.get('CLASS', msg.get('TXTENTRYCLASS', ''))
            fd_section = (msg.get('ARRL_SECT', '') or msg.get('SECTION', '') or
                         msg.get('TXTENTRYARRLSECT', '') or msg.get('TXTENTRYSECTION', '') or
                         msg.get('STATE', ''))
            if fd_class and fd_section:
                exchange = f"{fd_class} {fd_section}"
        parsed = parse_exchange(exchange)
        if parsed:
            fd_class, fd_section = parsed
            report = f"{fd_class.lower()} {fd_section.lower()}"
        else:
            report = exchange.lower() if exchange else ""
        # Use None for timestamp — let FDLog use its own now() for consistency
        timestamp = None
        print(f"{self._log_prefix}: QSO logged - {call} on {band_mode}, exchange: {report}")
        self.on_qso_logged(call, band_mode, report, timestamp)

    def _handle_band_change(self, msg: Dict[str, str]):
        """Process a READBMFRESPONSE — band/mode/freq update."""
        freq_str = msg.get('FREQ', '0')
        try:
            freq_hz = int(float(freq_str))
        except ValueError:
            freq_hz = 0
        band = freq_to_band(freq_hz) if freq_hz else None
        # N3FJP often sends FREQ=0 but provides BAND and MODE fields
        if not band:
            band_str = msg.get('BAND', '')
            mode_str = msg.get('MODE', msg.get('MODETEST', 'PH'))
            suffix = _mode_suffix(mode_str)
            if band_str:
                band = band_str.replace('m', '').replace('M', '').replace('cm', '') + suffix
        if band and band != self._current_band:
            self._current_band = band
            if self.config.auto_band and self.on_band_change:
                self.on_band_change(band)
            # Show just the band number in status
            band_num = band[:-1]  # strip mode suffix
            self.on_status_update(f"Connected ({band_num}m)")


# ---------------------------------------------------------------------------
# N3FJP Server — accept connections from N3FJP-compatible programs
# ---------------------------------------------------------------------------

class _N3FJPHandler(socketserver.StreamRequestHandler):
    """Handler for one connected N3FJP client."""

    def handle(self):
        server: N3FJPServer = self.server  # type: ignore[assignment]
        addr = f"{self.client_address[0]}:{self.client_address[1]}"
        print(f"N3FJP-Server: Client connected from {addr}")
        server._clients.add(self)
        server._update_status()
        buf = ""
        # Accumulator for UPDATE+ENTER pattern
        pending_fields: Dict[str, str] = {}
        try:
            while server._serving:
                try:
                    data = self.request.recv(4096)
                    if not data:
                        break
                    buf += data.decode('utf-8', errors='replace')
                    messages = parse_messages(buf)
                    last_end = buf.rfind('</CMD>')
                    if last_end >= 0:
                        buf = buf[last_end + 6:]
                    for msg in messages:
                        self._handle_msg(msg, pending_fields, server)
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            server._clients.discard(self)
            server._update_status()
            print(f"N3FJP-Server: Client disconnected from {addr}")

    def _handle_msg(self, msg: Dict[str, str], pending_fields: Dict[str, str], server: 'N3FJPServer'):
        cmd = msg.get('_type', '')

        if cmd == 'PROGRAM':
            # Client identifying itself
            self._send(build_cmd("PROGRAM", PROGRAM="FDLog Enhanced", VER="1.0"))
        elif cmd == 'APIVER':
            self._send(build_cmd("APIVER", VER="1.0"))
        elif cmd == 'READBMF':
            # Respond with current band/mode/freq
            info = server._get_current_info()
            self._send(build_cmd("READBMFRESPONSE",
                                 BAND=info.get('band', ''),
                                 MODE=info.get('mode', ''),
                                 FREQ=info.get('freq', '0')))
        elif cmd == 'QSOCOUNT':
            count = server._get_qso_count()
            self._send(build_cmd("QSOCOUNT", COUNT=str(count)))
        elif cmd == 'DUPECHECK':
            call = msg.get('CALL', '')
            band_mode = msg.get('BANDMODE', '')
            is_dupe = server._check_dupe(call, band_mode)
            self._send(build_cmd("DUPECHECKRESPONSE",
                                 CALL=call, DUPE="TRUE" if is_dupe else "FALSE"))
        elif cmd == 'UPDATE':
            # Accumulate fields for upcoming ENTER
            for k, v in msg.items():
                if k != '_type':
                    pending_fields[k] = v
        elif cmd == 'ENTER':
            # Log the QSO from accumulated fields
            if pending_fields:
                server._log_from_fields(pending_fields)
                pending_fields.clear()
        elif cmd == 'ADDADIFRECORD':
            adif_str = msg.get('ADIF', msg.get('_value', ''))
            if adif_str:
                server._log_from_adif(adif_str)
        elif cmd == 'CONTESTEX':
            # Parse contest exchange and log
            server._log_from_fields(msg)
        elif cmd in ('CHANGEFREQ', 'CHANGEBM'):
            freq_str = msg.get('FREQ', '0')
            try:
                freq_hz = int(float(freq_str))
            except ValueError:
                return
            band = freq_to_band(freq_hz)
            if band and server.on_band_change:
                server.on_band_change(band)
        elif cmd == 'SETUPDATESTATE':
            pass  # acknowledged implicitly

    def _send(self, msg: str):
        try:
            self.request.sendall(msg.encode('utf-8'))
        except Exception:
            pass


class N3FJPServer:
    """TCP server that accepts N3FJP-compatible client connections."""

    _log_prefix = "N3FJP-Server"

    def __init__(self, config: N3FJPConfig, on_qso_logged: Callable,
                 on_status_update: Callable, on_band_change: Optional[Callable] = None,
                 get_current_info: Optional[Callable] = None,
                 get_qso_count: Optional[Callable] = None,
                 check_dupe: Optional[Callable] = None):
        self.config = config
        self.on_qso_logged = on_qso_logged
        self.on_status_update = on_status_update
        self.on_band_change = on_band_change
        self._get_current_info_cb = get_current_info
        self._get_qso_count_cb = get_qso_count
        self._check_dupe_cb = check_dupe
        self._server: Optional[socketserver.ThreadingTCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._serving = False
        self._clients: set = set()

    def start(self):
        if self._serving:
            return
        try:
            self._server = socketserver.ThreadingTCPServer(
                (self.config.host, self.config.server_port), _N3FJPHandler)
            self._server.timeout = 1.0
            self._server.daemon_threads = True
            # Store reference to self on the server so handlers can access it
            self._server._serving = True  # type: ignore
            self._server._clients = self._clients  # type: ignore
            self._server._update_status = self._update_status  # type: ignore
            self._server._get_current_info = self._get_current_info  # type: ignore
            self._server._get_qso_count = self._get_qso_count  # type: ignore
            self._server._check_dupe = self._check_dupe  # type: ignore
            self._server._log_from_fields = self._log_from_fields  # type: ignore
            self._server._log_from_adif = self._log_from_adif  # type: ignore
            self._server.on_band_change = self.on_band_change  # type: ignore
        except OSError as e:
            print(f"{self._log_prefix}: Failed to start - {e}")
            self.on_status_update("Error")
            return
        self._serving = True
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()
        self.on_status_update("Listening")
        print(f"{self._log_prefix}: Listening on {self.config.host}:{self.config.server_port}")

    def stop(self):
        self._serving = False
        if self._server:
            self._server._serving = False  # type: ignore
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._clients.clear()
        self.on_status_update("Off")
        print(f"{self._log_prefix}: Stopped")

    def is_running(self) -> bool:
        return self._serving

    def get_status(self) -> dict:
        return {
            'running': self._serving,
            'clients': len(self._clients),
        }

    def broadcast(self, msg: str):
        """Send a message to all connected clients."""
        for handler in list(self._clients):
            try:
                handler.request.sendall(msg.encode('utf-8'))
            except Exception:
                pass

    def _serve_loop(self):
        while self._serving:
            self._server.handle_request()

    def _update_status(self):
        n = len(self._clients)
        if n == 0:
            self.on_status_update("Listening")
        else:
            self.on_status_update(f"Serving ({n} client{'s' if n != 1 else ''})")

    def _get_current_info(self) -> dict:
        if self._get_current_info_cb:
            return self._get_current_info_cb()
        return {'band': '', 'mode': '', 'freq': '0'}

    def _get_qso_count(self) -> int:
        if self._get_qso_count_cb:
            return self._get_qso_count_cb()
        return 0

    def _check_dupe(self, call: str, band_mode: str) -> bool:
        if self._check_dupe_cb:
            return self._check_dupe_cb(call, band_mode)
        return False

    def _log_from_fields(self, fields: Dict[str, str]):
        """Log a QSO from accumulated UPDATE fields."""
        call = fields.get('TXTENTRYCALL', fields.get('CALL', '')).strip().upper()
        if not call:
            return
        freq_str = fields.get('FREQ', '0')
        try:
            freq_hz = int(float(freq_str))
        except ValueError:
            freq_hz = 0
        mode = fields.get('MODE', fields.get('TXTENTRYMODE', 'SSB'))
        band_mode = freq_to_band(freq_hz) if freq_hz else None
        if not band_mode:
            band_str = fields.get('BAND', fields.get('TXTENTRYBAND', ''))
            suffix = _mode_suffix(mode)
            if band_str:
                band_mode = band_str.replace('m', '').replace('M', '') + suffix
        if not band_mode:
            print(f"{self._log_prefix}: Cannot determine band for {call}")
            return
        exchange = fields.get('EXCHANGE', fields.get('TXTENTRYEXCHANGE', ''))
        parsed = parse_exchange(exchange)
        if parsed:
            fd_class, fd_section = parsed
            report = f"{fd_class.lower()} {fd_section.lower()}"
        else:
            report = exchange.lower() if exchange else ""
        timestamp = fields.get('TIME', datetime.now(timezone.utc).strftime("%H%M"))
        timestamp = timestamp.replace(':', '')[:4]
        print(f"{self._log_prefix}: QSO from client - {call} on {band_mode}, exchange: {report}")
        self.on_qso_logged(call, band_mode, report, timestamp)

    def _log_from_adif(self, adif_str: str):
        """Log a QSO from an ADIF record."""
        fields = parse_adif(adif_str)
        call = fields.get('CALL', '').strip().upper()
        if not call:
            return
        freq_str = fields.get('FREQ', '0')
        try:
            # ADIF FREQ is in MHz
            freq_hz = int(float(freq_str) * 1_000_000) if '.' in freq_str or float(freq_str) < 1000 else int(float(freq_str))
        except ValueError:
            freq_hz = 0
        mode = fields.get('MODE', 'SSB')
        band_mode = freq_to_band(freq_hz) if freq_hz else None
        if not band_mode:
            band_str = fields.get('BAND', '')
            suffix = _mode_suffix(mode)
            if band_str:
                band_mode = band_str.replace('m', '').replace('M', '') + suffix
        if not band_mode:
            print(f"{self._log_prefix}: Cannot determine band for {call} from ADIF")
            return
        exchange = fields.get('SRX_STRING', fields.get('COMMENT', ''))
        parsed = parse_exchange(exchange)
        if parsed:
            fd_class, fd_section = parsed
            report = f"{fd_class.lower()} {fd_section.lower()}"
        else:
            report = exchange.lower() if exchange else ""
        time_str = fields.get('TIME_ON', datetime.now(timezone.utc).strftime("%H%M"))
        timestamp = time_str.replace(':', '')[:4]
        print(f"{self._log_prefix}: QSO from ADIF - {call} on {band_mode}, exchange: {report}")
        self.on_qso_logged(call, band_mode, report, timestamp)


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

try:
    import tkinter as tk
    from tkinter import ttk
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False


class N3FJPSettingsDialog:
    """Tkinter dialog for N3FJP integration settings."""

    def __init__(self, parent, config: N3FJPConfig,
                 client: Optional[N3FJPClient], server: Optional[N3FJPServer],
                 on_save: Callable):
        if not _TK_AVAILABLE:
            return
        self.config = config
        self.client = client
        self.server = server
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("N3FJP Integration Settings")
        self.win.geometry("420x480")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        frame = ttk.Frame(self.win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        # --- Client Section ---
        ttk.Label(frame, text="Client (connect to N3FJP)", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(5, 2))
        row += 1

        self.client_enabled_var = tk.BooleanVar(value=config.client_enabled)
        ttk.Checkbutton(frame, text="Enable Client", variable=self.client_enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=3)
        row += 1

        ttk.Label(frame, text="Host:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.host_var = tk.StringVar(value=config.host)
        ttk.Entry(frame, textvariable=self.host_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1

        ttk.Label(frame, text="Client Port:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.client_port_var = tk.StringVar(value=str(config.client_port))
        ttk.Entry(frame, textvariable=self.client_port_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1

        # Client status
        client_status = "Disconnected"
        client_color = "gray"
        if client and client.is_connected():
            client_status = "Connected"
            client_color = "green"
        elif client and client._running:
            client_status = "Connecting..."
            client_color = "orange"
        self.client_status_lbl = ttk.Label(frame, text=f"Client: {client_status}", foreground=client_color)
        self.client_status_lbl.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=3)
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=8)
        row += 1

        # --- Server Section ---
        ttk.Label(frame, text="Server (accept N3FJP clients)", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(5, 2))
        row += 1

        self.server_enabled_var = tk.BooleanVar(value=config.server_enabled)
        ttk.Checkbutton(frame, text="Enable Server", variable=self.server_enabled_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=3)
        row += 1

        ttk.Label(frame, text="Server Port:").grid(row=row, column=0, sticky=tk.W, pady=3)
        self.server_port_var = tk.StringVar(value=str(config.server_port))
        ttk.Entry(frame, textvariable=self.server_port_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=3)
        row += 1

        # Server status
        server_status = "Off"
        server_color = "gray"
        if server and server.is_running():
            n = len(server._clients)
            server_status = f"Listening ({n} clients)" if n else "Listening"
            server_color = "green"
        self.server_status_lbl = ttk.Label(frame, text=f"Server: {server_status}", foreground=server_color)
        self.server_status_lbl.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=3)
        row += 1

        ttk.Separator(frame).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=8)
        row += 1

        # --- Common Options ---
        self.auto_log_var = tk.BooleanVar(value=config.auto_log)
        ttk.Checkbutton(frame, text="Auto-log QSOs", variable=self.auto_log_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        self.auto_band_var = tk.BooleanVar(value=config.auto_band)
        ttk.Checkbutton(frame, text="Auto-switch band", variable=self.auto_band_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        try:
            cport = int(self.client_port_var.get())
        except ValueError:
            cport = 1100
        try:
            sport = int(self.server_port_var.get())
        except ValueError:
            sport = 1100
        self.config.client_enabled = self.client_enabled_var.get()
        self.config.server_enabled = self.server_enabled_var.get()
        self.config.host = self.host_var.get().strip() or "127.0.0.1"
        self.config.client_port = cport
        self.config.server_port = sport
        self.config.auto_log = self.auto_log_var.get()
        self.config.auto_band = self.auto_band_var.get()
        self.on_save(self.config)
        self.win.destroy()
