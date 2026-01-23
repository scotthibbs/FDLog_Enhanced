"""
CW Keying Interface for FDLog_Enhanced
Compatible with N3FJP-style DTR/RTS keying, with optional Winkeyer support.
"""

import threading
import time
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List

# Try to import pyserial
try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False

# Morse code dictionary
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    '/': '-..-.', '-': '-....-', '=': '-...-', '+': '.-.-.', '@': '.--.-.',
    ' ': ' '
}

# Prosigns (sent without inter-character spacing)
PROSIGNS = {
    'AR': '.-.-.',      # End of message
    'AS': '.-...',      # Wait
    'BK': '-...-.-',    # Break
    'BT': '-...-',      # New paragraph (=)
    'CL': '-.-..-..',   # Closing station
    'CT': '-.-.-',      # Attention
    'KN': '-.--.',      # Go ahead, specific station
    'SK': '...-.-',     # End of contact
    'SN': '...-.',      # Understood
}


@dataclass
class CWConfig:
    """CW keying configuration settings."""
    port: str = ""
    method: str = "DTR"  # DTR, RTS, or WINKEYER
    wpm: int = 20
    ptt_lead: int = 50   # ms before keying
    ptt_tail: int = 50   # ms after keying
    ptt_enabled: bool = False
    ptt_line: str = "RTS"  # RTS or DTR (opposite of key line)
    weight: int = 50     # dit/dah weight percentage (50 = standard)

    # Winkeyer settings
    winkeyer_version: int = 0
    sidetone_freq: int = 600
    sidetone_enabled: bool = True

    # CAT keying settings
    cat_enabled: bool = False
    cat_port: str = ""
    cat_baud: int = 9600
    cat_rig: str = ""  # "FLEX", "ICOM7300", "ICOM7610"

    def copy(self) -> 'CWConfig':
        """Create a copy of this config."""
        return CWConfig(
            port=self.port, method=self.method, wpm=self.wpm,
            ptt_lead=self.ptt_lead, ptt_tail=self.ptt_tail,
            ptt_enabled=self.ptt_enabled, ptt_line=self.ptt_line,
            weight=self.weight, winkeyer_version=self.winkeyer_version,
            sidetone_freq=self.sidetone_freq, sidetone_enabled=self.sidetone_enabled,
            cat_enabled=self.cat_enabled, cat_port=self.cat_port,
            cat_baud=self.cat_baud, cat_rig=self.cat_rig
        )


@dataclass
class CWMessage:
    """A CW message to be sent."""
    text: str
    priority: int = 0  # Higher priority = sent first
    callback: Optional[Callable] = None  # Called when complete


class CWKeyer(ABC):
    """Abstract base class for CW keyers."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the keyer. Returns True on success."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the keyer."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if keyer is connected."""
        pass

    @abstractmethod
    def key_down(self) -> None:
        """Key down (transmit)."""
        pass

    @abstractmethod
    def key_up(self) -> None:
        """Key up (stop transmit)."""
        pass

    @abstractmethod
    def set_wpm(self, wpm: int) -> None:
        """Set speed in words per minute."""
        pass

    @abstractmethod
    def send_char(self, char: str, dit_time: float) -> bool:
        """Send a single character. Returns False if aborted."""
        pass

    @abstractmethod
    def abort(self) -> None:
        """Abort current transmission."""
        pass


class SerialKeyer(CWKeyer):
    """Serial port DTR/RTS keyer implementation."""

    def __init__(self, config: CWConfig):
        self.config = config
        self.port: Optional[serial.Serial] = None
        self.lock = threading.RLock()
        self._aborted = False
        self._wpm = config.wpm

    def connect(self) -> bool:
        """Connect to the serial port."""
        if not PYSERIAL_AVAILABLE:
            return False

        with self.lock:
            try:
                self.port = serial.Serial()
                self.port.port = self.config.port
                self.port.baudrate = 9600
                self.port.timeout = 0.1
                self.port.open()
                # Initialize lines to off
                self.port.dtr = False
                self.port.rts = False
                self._aborted = False
                return True
            except (serial.SerialException, OSError) as e:
                print(f"CW: Failed to open port {self.config.port}: {e}")
                self.port = None
                return False

    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        with self.lock:
            if self.port and self.port.is_open:
                try:
                    self.port.dtr = False
                    self.port.rts = False
                    self.port.close()
                except:
                    pass
            self.port = None

    def is_connected(self) -> bool:
        """Check if connected."""
        with self.lock:
            return self.port is not None and self.port.is_open

    def key_down(self) -> None:
        """Key down using configured method."""
        with self.lock:
            if not self.port:
                return
            try:
                if self.config.method == "DTR":
                    self.port.dtr = True
                else:  # RTS
                    self.port.rts = True
            except:
                pass

    def key_up(self) -> None:
        """Key up using configured method."""
        with self.lock:
            if not self.port:
                return
            try:
                if self.config.method == "DTR":
                    self.port.dtr = False
                else:  # RTS
                    self.port.rts = False
            except:
                pass

    def ptt_on(self) -> None:
        """Enable PTT using configured line."""
        if not self.config.ptt_enabled:
            return
        with self.lock:
            if not self.port:
                return
            try:
                if self.config.ptt_line == "RTS":
                    self.port.rts = True
                else:  # DTR
                    self.port.dtr = True
            except:
                pass

    def ptt_off(self) -> None:
        """Disable PTT using configured line."""
        if not self.config.ptt_enabled:
            return
        with self.lock:
            if not self.port:
                return
            try:
                if self.config.ptt_line == "RTS":
                    self.port.rts = False
                else:  # DTR
                    self.port.dtr = False
            except:
                pass

    def set_wpm(self, wpm: int) -> None:
        """Set speed in words per minute."""
        self._wpm = max(5, min(60, wpm))

    def get_dit_time(self) -> float:
        """Calculate dit duration in seconds for current WPM."""
        # PARIS standard: 50 dit-units per word
        # dit_time = 60 / (wpm * 50) = 1.2 / wpm
        return 1.2 / self._wpm

    def send_char(self, char: str, dit_time: float) -> bool:
        """Send a single character. Returns False if aborted."""
        char = char.upper()

        if char == ' ':
            # Word space: 7 dit times (we already have 3 from char space)
            # So add 4 more dit times
            time.sleep(dit_time * 4)
            return not self._aborted

        if char not in MORSE_CODE:
            return not self._aborted

        code = MORSE_CODE[char]

        for i, element in enumerate(code):
            if self._aborted:
                self.key_up()
                return False

            if element == '.':
                self.key_down()
                time.sleep(dit_time)
                self.key_up()
            elif element == '-':
                self.key_down()
                time.sleep(dit_time * 3)
                self.key_up()

            # Inter-element space (1 dit time) except after last element
            if i < len(code) - 1:
                time.sleep(dit_time)

        # Inter-character space (3 dit times)
        time.sleep(dit_time * 3)
        return not self._aborted

    def abort(self) -> None:
        """Abort current transmission."""
        self._aborted = True
        self.key_up()

    def reset_abort(self) -> None:
        """Reset abort flag."""
        self._aborted = False


class WinkeyerKeyer(CWKeyer):
    """Winkeyer protocol implementation (K1EL Winkeyer)."""

    # Winkeyer commands
    CMD_ADMIN = 0x00
    CMD_SIDETONE = 0x01
    CMD_SPEED = 0x02
    CMD_WEIGHT = 0x03
    CMD_PTT_LEAD_IN = 0x04
    CMD_SPEED_POT = 0x05
    CMD_PAUSE = 0x06
    CMD_GET_SPEED = 0x07
    CMD_BACKSPACE = 0x08
    CMD_PIN_CONFIG = 0x09
    CMD_CLEAR_BUFFER = 0x0A
    CMD_KEY_IMMEDIATE = 0x0B
    CMD_HSCW_SPEED = 0x0C
    CMD_FARNSWORTH = 0x0D
    CMD_WINKEYER2_MODE = 0x0E
    CMD_LOAD_DEFAULTS = 0x0F
    CMD_FIRST_EXT = 0x10
    CMD_KEY_BUFFERED = 0x11
    CMD_WAIT = 0x12
    CMD_MERGE_LETTERS = 0x13
    CMD_BUFFER_SPEED = 0x14
    CMD_HSCW_SPEED_BUFFERED = 0x15
    CMD_CANCEL_BUFFER_SPEED = 0x16
    CMD_BUFFERED_PTT = 0x17

    # Admin sub-commands
    ADMIN_CALIBRATE = 0x00
    ADMIN_RESET = 0x01
    ADMIN_HOST_OPEN = 0x02
    ADMIN_HOST_CLOSE = 0x03
    ADMIN_ECHO = 0x04
    ADMIN_PADDLE_A2D = 0x05
    ADMIN_SPEED_A2D = 0x06
    ADMIN_GET_VALUES = 0x07
    ADMIN_GET_CAL = 0x09
    ADMIN_SET_WK1_MODE = 0x0A
    ADMIN_SET_WK2_MODE = 0x0B
    ADMIN_DUMP_EEPROM = 0x0C
    ADMIN_LOAD_EEPROM = 0x0D
    ADMIN_SEND_MSG = 0x0E
    ADMIN_LOAD_X1MODE = 0x0F
    ADMIN_FIRMWARE_UPDATE = 0x10
    ADMIN_SET_HIGH_BAUD = 0x11
    ADMIN_SET_LOW_BAUD = 0x12
    ADMIN_SET_K1EL_MODE = 0x13

    def __init__(self, config: CWConfig):
        self.config = config
        self.port: Optional[serial.Serial] = None
        self.lock = threading.RLock()
        self._aborted = False
        self._wpm = config.wpm
        self.version = 0
        self._echo_char = None
        self._status = 0

    def connect(self) -> bool:
        """Connect to Winkeyer."""
        if not PYSERIAL_AVAILABLE:
            return False

        with self.lock:
            try:
                self.port = serial.Serial()
                self.port.port = self.config.port
                self.port.baudrate = 1200
                self.port.bytesize = serial.EIGHTBITS
                self.port.parity = serial.PARITY_NONE
                self.port.stopbits = serial.STOPBITS_TWO
                self.port.timeout = 0.5
                self.port.open()

                # Host open command
                self.port.write(bytes([self.CMD_ADMIN, self.ADMIN_HOST_OPEN]))
                time.sleep(0.1)

                # Read version
                response = self.port.read(1)
                if response:
                    self.version = response[0]
                    self.config.winkeyer_version = self.version
                    print(f"CW: Winkeyer version {self.version} detected")
                else:
                    print("CW: No response from Winkeyer")
                    self.port.close()
                    self.port = None
                    return False

                # Set initial speed
                self.set_wpm(self._wpm)

                # Set sidetone
                if self.config.sidetone_enabled:
                    self._set_sidetone(self.config.sidetone_freq)

                self._aborted = False
                return True

            except (serial.SerialException, OSError) as e:
                print(f"CW: Failed to open Winkeyer port {self.config.port}: {e}")
                self.port = None
                return False

    def disconnect(self) -> None:
        """Disconnect from Winkeyer."""
        with self.lock:
            if self.port and self.port.is_open:
                try:
                    # Clear buffer
                    self.port.write(bytes([self.CMD_CLEAR_BUFFER]))
                    # Host close
                    self.port.write(bytes([self.CMD_ADMIN, self.ADMIN_HOST_CLOSE]))
                    time.sleep(0.1)
                    self.port.close()
                except:
                    pass
            self.port = None
            self.version = 0

    def is_connected(self) -> bool:
        """Check if connected."""
        with self.lock:
            return self.port is not None and self.port.is_open and self.version > 0

    def key_down(self) -> None:
        """Key down (immediate keying)."""
        with self.lock:
            if not self.port:
                return
            try:
                self.port.write(bytes([self.CMD_KEY_IMMEDIATE, 0x01]))
            except:
                pass

    def key_up(self) -> None:
        """Key up (immediate keying)."""
        with self.lock:
            if not self.port:
                return
            try:
                self.port.write(bytes([self.CMD_KEY_IMMEDIATE, 0x00]))
            except:
                pass

    def set_wpm(self, wpm: int) -> None:
        """Set speed in words per minute."""
        self._wpm = max(5, min(60, wpm))
        with self.lock:
            if not self.port:
                return
            try:
                self.port.write(bytes([self.CMD_SPEED, self._wpm]))
            except:
                pass

    def _set_sidetone(self, freq: int) -> None:
        """Set sidetone frequency."""
        # Winkeyer sidetone: 0=disabled, 1-127 maps to ~500Hz-4000Hz
        if freq < 500:
            value = 0
        else:
            value = min(127, max(1, (freq - 500) // 28 + 1))
        with self.lock:
            if self.port:
                try:
                    self.port.write(bytes([self.CMD_SIDETONE, value]))
                except:
                    pass

    def send_char(self, char: str, dit_time: float) -> bool:
        """Send a character via Winkeyer buffered sending."""
        if self._aborted:
            return False

        char = char.upper()

        with self.lock:
            if not self.port:
                return False
            try:
                # Send character directly - Winkeyer handles timing
                if char == ' ':
                    self.port.write(bytes([ord(' ')]))
                elif char.isalnum() or char in '.,?/-=+@':
                    self.port.write(bytes([ord(char)]))
                # Wait for character to be sent (approximate)
                time.sleep(dit_time * 10)  # Approximate character time
            except:
                return False

        return not self._aborted

    def send_text(self, text: str) -> bool:
        """Send text via Winkeyer buffered sending."""
        with self.lock:
            if not self.port:
                return False
            try:
                for char in text.upper():
                    if self._aborted:
                        self.abort()
                        return False
                    if char.isalnum() or char in ' .,?/-=+@':
                        self.port.write(bytes([ord(char)]))
                        time.sleep(0.01)  # Small delay between chars to not overflow buffer
                return True
            except:
                return False

    def abort(self) -> None:
        """Abort current transmission."""
        self._aborted = True
        with self.lock:
            if self.port:
                try:
                    self.port.write(bytes([self.CMD_CLEAR_BUFFER]))
                except:
                    pass

    def reset_abort(self) -> None:
        """Reset abort flag."""
        self._aborted = False


class CATKeyer(CWKeyer):
    """CAT command keying for modern rigs (Flex, Icom 7300/7610)."""

    def __init__(self, config: CWConfig):
        self.config = config
        self.port: Optional[serial.Serial] = None
        self.lock = threading.RLock()
        self._aborted = False
        self._wpm = config.wpm

    def connect(self) -> bool:
        """Connect to rig via CAT."""
        if not PYSERIAL_AVAILABLE:
            return False

        with self.lock:
            try:
                self.port = serial.Serial()
                self.port.port = self.config.cat_port
                self.port.baudrate = self.config.cat_baud
                self.port.timeout = 0.5

                # Configure serial settings based on rig
                if self.config.cat_rig.startswith("ICOM"):
                    self.port.bytesize = serial.EIGHTBITS
                    self.port.parity = serial.PARITY_NONE
                    self.port.stopbits = serial.STOPBITS_ONE
                else:  # FLEX and others
                    self.port.bytesize = serial.EIGHTBITS
                    self.port.parity = serial.PARITY_NONE
                    self.port.stopbits = serial.STOPBITS_ONE

                self.port.open()
                self._aborted = False
                return True

            except (serial.SerialException, OSError) as e:
                print(f"CW: Failed to open CAT port {self.config.cat_port}: {e}")
                self.port = None
                return False

    def disconnect(self) -> None:
        """Disconnect from rig."""
        with self.lock:
            if self.port and self.port.is_open:
                try:
                    self.port.close()
                except:
                    pass
            self.port = None

    def is_connected(self) -> bool:
        """Check if connected."""
        with self.lock:
            return self.port is not None and self.port.is_open

    def _send_icom_cw(self, text: str) -> None:
        """Send CW text via Icom CI-V protocol."""
        # CI-V CW message command: FE FE ra ta 17 <text> FD
        # ra = receiver address (typically 0x94 for 7300, 0x98 for 7610)
        # ta = transmitter address (typically 0xE0 for computer)

        rig_addr = 0x94 if self.config.cat_rig == "ICOM7300" else 0x98
        cmd = bytes([0xFE, 0xFE, rig_addr, 0xE0, 0x17]) + text.encode('ascii') + bytes([0xFD])

        with self.lock:
            if self.port:
                try:
                    self.port.write(cmd)
                except:
                    pass

    def _send_flex_cw(self, text: str) -> None:
        """Send CW text via FlexRadio CAT command."""
        # Flex SmartSDR CAT: ZZCW<text>;
        cmd = f"ZZCW{text};"

        with self.lock:
            if self.port:
                try:
                    self.port.write(cmd.encode('ascii'))
                except:
                    pass

    def key_down(self) -> None:
        """Key down via CAT."""
        # Not directly supported - use buffered sending instead
        pass

    def key_up(self) -> None:
        """Key up via CAT."""
        # Not directly supported - use buffered sending instead
        pass

    def set_wpm(self, wpm: int) -> None:
        """Set speed in words per minute via CAT."""
        self._wpm = max(5, min(60, wpm))

        with self.lock:
            if not self.port:
                return

            try:
                if self.config.cat_rig.startswith("ICOM"):
                    # CI-V key speed command: FE FE ra ta 14 0C <speed> FD
                    rig_addr = 0x94 if self.config.cat_rig == "ICOM7300" else 0x98
                    # Speed is BCD encoded
                    speed_bcd = ((wpm // 10) << 4) | (wpm % 10)
                    cmd = bytes([0xFE, 0xFE, rig_addr, 0xE0, 0x14, 0x0C, speed_bcd, 0xFD])
                    self.port.write(cmd)
                elif self.config.cat_rig == "FLEX":
                    cmd = f"ZZKS{wpm:02d};"
                    self.port.write(cmd.encode('ascii'))
            except:
                pass

    def send_char(self, char: str, dit_time: float) -> bool:
        """Send a single character via CAT."""
        if self._aborted:
            return False

        char = char.upper()

        if self.config.cat_rig.startswith("ICOM"):
            self._send_icom_cw(char)
        elif self.config.cat_rig == "FLEX":
            self._send_flex_cw(char)

        # Estimate time for character
        time.sleep(dit_time * 10)

        return not self._aborted

    def send_text(self, text: str) -> bool:
        """Send text via CAT (more efficient than char-by-char)."""
        if self._aborted:
            return False

        if self.config.cat_rig.startswith("ICOM"):
            self._send_icom_cw(text.upper())
        elif self.config.cat_rig == "FLEX":
            self._send_flex_cw(text.upper())

        return not self._aborted

    def abort(self) -> None:
        """Abort current transmission."""
        self._aborted = True
        # Send abort command if supported
        with self.lock:
            if self.port:
                try:
                    if self.config.cat_rig == "FLEX":
                        self.port.write(b"ZZCX;")  # Cancel CW
                except:
                    pass

    def reset_abort(self) -> None:
        """Reset abort flag."""
        self._aborted = False


class CWMessageQueue:
    """Thread-safe message queue for CW transmission."""

    def __init__(self):
        self.queue = queue.PriorityQueue()
        self._counter = 0
        self.lock = threading.Lock()

    def add(self, message: CWMessage) -> None:
        """Add a message to the queue."""
        with self.lock:
            # Use counter to maintain FIFO order for same priority
            self._counter += 1
            # Priority queue is min-heap, so negate priority for high-first
            self.queue.put((-message.priority, self._counter, message))

    def get(self, timeout: float = 0.1) -> Optional[CWMessage]:
        """Get next message from queue. Returns None if empty."""
        try:
            _, _, message = self.queue.get(timeout=timeout)
            return message
        except queue.Empty:
            return None

    def clear(self) -> None:
        """Clear all messages from queue."""
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()


class CWMacroManager:
    """Manages CW macros with variable substitution."""

    DEFAULT_MACROS = {
        'F1': 'CQ FD {MYCALL} {MYCALL}',
        'F2': '{CALL} {RST} {CLASS} {SECT}',
        'F3': 'TU {MYCALL}',
        'F4': '{CALL}',
        'F5': '{MYCALL}',
        'F6': '{RST}',
        'F7': '{CLASS}',
        'F8': '{SECT}',
        'F9': '73',
        'F10': 'QRZ?',
        'F11': 'AGN',
        'F12': 'TU QRZ?',
    }

    def __init__(self, get_variable_func: Optional[Callable[[str], str]] = None):
        """
        Initialize macro manager.

        Args:
            get_variable_func: Function that takes a variable name and returns its value
        """
        self.macros = dict(self.DEFAULT_MACROS)
        self.get_variable = get_variable_func or (lambda x: f"{{{x}}}")

    def set_macro(self, key: str, value: str) -> None:
        """Set a macro."""
        self.macros[key.upper()] = value

    def get_macro(self, key: str) -> str:
        """Get a macro (raw, without substitution)."""
        return self.macros.get(key.upper(), '')

    def expand_macro(self, key: str) -> str:
        """Get a macro with variable substitution."""
        raw = self.get_macro(key)
        return self.substitute_variables(raw)

    def substitute_variables(self, text: str) -> str:
        """Replace {VARIABLE} patterns with actual values."""
        import re

        def replace_var(match):
            var_name = match.group(1)
            return self.get_variable(var_name)

        return re.sub(r'\{(\w+)\}', replace_var, text)

    def get_all_macros(self) -> Dict[str, str]:
        """Get all macros."""
        return dict(self.macros)

    def load_from_dict(self, data: Dict[str, str]) -> None:
        """Load macros from a dictionary."""
        for key, value in data.items():
            if key.upper().startswith('F') and key[1:].isdigit():
                self.macros[key.upper()] = value

    def to_dict(self) -> Dict[str, str]:
        """Export macros to a dictionary."""
        return dict(self.macros)


class CWController:
    """Main CW keying controller."""

    def __init__(self, config: CWConfig, root=None, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize CW controller.

        Args:
            config: CW configuration
            root: Tkinter root window (for after() calls)
            status_callback: Function to call with status updates
        """
        self.config = config
        self.root = root
        self.status_callback = status_callback

        self.keyer: Optional[CWKeyer] = None
        self.message_queue = CWMessageQueue()
        self.macro_manager = CWMacroManager()

        self._sending = False
        self._current_message = ""
        self._current_char_index = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.lock = threading.RLock()

    def set_variable_getter(self, func: Callable[[str], str]) -> None:
        """Set the function used to get variable values."""
        self.macro_manager.get_variable = func

    def create_keyer(self) -> Optional[CWKeyer]:
        """Create appropriate keyer based on config."""
        if self.config.method == "WINKEYER":
            return WinkeyerKeyer(self.config)
        elif self.config.cat_enabled:
            return CATKeyer(self.config)
        else:
            return SerialKeyer(self.config)

    def connect(self) -> bool:
        """Connect to the keyer."""
        with self.lock:
            if self.keyer and self.keyer.is_connected():
                return True

            self.keyer = self.create_keyer()
            if not self.keyer:
                self._update_status("No keyer available")
                return False

            if self.keyer.connect():
                self._start_thread()
                self._update_status(f"Connected to {self.config.port}")
                return True
            else:
                self._update_status(f"Failed to connect to {self.config.port}")
                return False

    def disconnect(self) -> None:
        """Disconnect from the keyer."""
        with self.lock:
            self._stop_thread()
            if self.keyer:
                self.keyer.disconnect()
                self.keyer = None
            self._update_status("Disconnected")

    def is_connected(self) -> bool:
        """Check if connected."""
        with self.lock:
            return self.keyer is not None and self.keyer.is_connected()

    def is_sending(self) -> bool:
        """Check if currently sending."""
        return self._sending

    def send_text(self, text: str, priority: int = 0, callback: Optional[Callable] = None) -> None:
        """Queue text for sending."""
        message = CWMessage(text=text, priority=priority, callback=callback)
        self.message_queue.add(message)

    def send_macro(self, key: str, priority: int = 0, callback: Optional[Callable] = None) -> None:
        """Queue a macro for sending."""
        text = self.macro_manager.expand_macro(key)
        if text:
            self.send_text(text, priority, callback)

    def abort(self) -> None:
        """Abort current and queued transmissions."""
        self.message_queue.clear()
        if self.keyer:
            self.keyer.abort()
        self._sending = False
        self._update_status("Aborted")

    def set_wpm(self, wpm: int) -> None:
        """Set speed in words per minute."""
        self.config.wpm = max(5, min(60, wpm))
        if self.keyer:
            self.keyer.set_wpm(self.config.wpm)
        self._update_status(f"{self.config.wpm} WPM")

    def adjust_wpm(self, delta: int) -> None:
        """Adjust WPM by delta amount."""
        self.set_wpm(self.config.wpm + delta)

    def _start_thread(self) -> None:
        """Start the keying thread."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._keying_thread, daemon=True)
        self._thread.start()

    def _stop_thread(self) -> None:
        """Stop the keying thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _keying_thread(self) -> None:
        """Thread that processes the message queue and sends CW."""
        while not self._stop_event.is_set():
            if not self.keyer or not self.keyer.is_connected():
                time.sleep(0.1)
                continue

            message = self.message_queue.get(timeout=0.1)
            if not message:
                continue

            self._send_message(message)

    def _send_message(self, message: CWMessage) -> None:
        """Send a single message."""
        self._sending = True
        self._current_message = message.text
        self._current_char_index = 0

        if self.keyer:
            self.keyer.reset_abort()

        # Handle PTT lead-in
        if isinstance(self.keyer, SerialKeyer) and self.config.ptt_enabled:
            self.keyer.ptt_on()
            time.sleep(self.config.ptt_lead / 1000.0)

        dit_time = 1.2 / self.config.wpm

        self._update_status(f"Sending: {message.text}")

        # Check if keyer supports bulk text sending
        if isinstance(self.keyer, (WinkeyerKeyer, CATKeyer)):
            # Use bulk send for these keyers
            self.keyer.send_text(message.text)
        else:
            # Send character by character for serial keyer
            for i, char in enumerate(message.text):
                if self._stop_event.is_set():
                    break

                self._current_char_index = i

                if not self.keyer.send_char(char, dit_time):
                    break  # Aborted

        # Handle PTT tail
        if isinstance(self.keyer, SerialKeyer) and self.config.ptt_enabled:
            time.sleep(self.config.ptt_tail / 1000.0)
            self.keyer.ptt_off()

        self._sending = False
        self._current_message = ""

        if message.callback:
            if self.root:
                self.root.after(0, message.callback)
            else:
                message.callback()

        self._update_status("Ready")

    def _update_status(self, status: str) -> None:
        """Update status display."""
        if self.status_callback:
            if self.root:
                self.root.after(0, lambda: self.status_callback(status))
            else:
                self.status_callback(status)


def list_serial_ports() -> List[str]:
    """Get list of available serial ports."""
    if not PYSERIAL_AVAILABLE:
        return []

    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(port.device)
    return sorted(ports)


# Tkinter dialogs (only created if tkinter is available)
try:
    from tkinter import Toplevel, Frame, Label, Entry, Button, StringVar, IntVar
    from tkinter import OptionMenu, Checkbutton, Spinbox, messagebox
    from tkinter import W, E, EW, NSEW, END
    from tkinter import ttk

    TKINTER_AVAILABLE = True

    class CWSettingsDialog:
        """Settings dialog for CW configuration."""

        def __init__(self, parent, config: CWConfig, on_save: Optional[Callable[[CWConfig], None]] = None):
            self.parent = parent
            self.config = config.copy()
            self.on_save = on_save
            self.result = None

            self.dialog = Toplevel(parent)
            self.dialog.title("CW Settings")
            self.dialog.transient(parent)
            self.dialog.grab_set()

            self._create_widgets()
            self._center_window()

        def _create_widgets(self):
            frame = Frame(self.dialog, padx=10, pady=10)
            frame.pack(fill='both', expand=True)

            row = 0

            # Port selection
            Label(frame, text="COM Port:").grid(row=row, column=0, sticky=W, pady=2)
            self.port_var = StringVar(value=self.config.port)
            ports = list_serial_ports()
            if not ports:
                ports = ["No ports found"]
            if self.config.port and self.config.port not in ports:
                ports.insert(0, self.config.port)
            self.port_menu = ttk.Combobox(frame, textvariable=self.port_var, values=ports, width=15)
            self.port_menu.grid(row=row, column=1, sticky=EW, pady=2)

            Button(frame, text="Refresh", command=self._refresh_ports).grid(row=row, column=2, padx=5)
            row += 1

            # Keying method
            Label(frame, text="Keying Method:").grid(row=row, column=0, sticky=W, pady=2)
            self.method_var = StringVar(value=self.config.method)
            methods = ["DTR", "RTS", "WINKEYER"]
            self.method_menu = ttk.Combobox(frame, textvariable=self.method_var, values=methods, width=15, state='readonly')
            self.method_menu.grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            # WPM
            Label(frame, text="Speed (WPM):").grid(row=row, column=0, sticky=W, pady=2)
            self.wpm_var = IntVar(value=self.config.wpm)
            self.wpm_spin = Spinbox(frame, from_=5, to=60, textvariable=self.wpm_var, width=10)
            self.wpm_spin.grid(row=row, column=1, sticky=W, pady=2)
            row += 1

            # PTT settings
            self.ptt_var = IntVar(value=1 if self.config.ptt_enabled else 0)
            Checkbutton(frame, text="Enable PTT", variable=self.ptt_var).grid(row=row, column=0, columnspan=2, sticky=W, pady=2)
            row += 1

            Label(frame, text="PTT Line:").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_line_var = StringVar(value=self.config.ptt_line)
            self.ptt_line_menu = ttk.Combobox(frame, textvariable=self.ptt_line_var, values=["RTS", "DTR"], width=15, state='readonly')
            self.ptt_line_menu.grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            Label(frame, text="PTT Lead-in (ms):").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_lead_var = IntVar(value=self.config.ptt_lead)
            Spinbox(frame, from_=0, to=500, textvariable=self.ptt_lead_var, width=10).grid(row=row, column=1, sticky=W, pady=2)
            row += 1

            Label(frame, text="PTT Tail (ms):").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_tail_var = IntVar(value=self.config.ptt_tail)
            Spinbox(frame, from_=0, to=500, textvariable=self.ptt_tail_var, width=10).grid(row=row, column=1, sticky=W, pady=2)
            row += 1

            # Separator
            ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=EW, pady=10)
            row += 1

            # CAT keying settings
            self.cat_var = IntVar(value=1 if self.config.cat_enabled else 0)
            Checkbutton(frame, text="Enable CAT Keying", variable=self.cat_var).grid(row=row, column=0, columnspan=2, sticky=W, pady=2)
            row += 1

            Label(frame, text="CAT Port:").grid(row=row, column=0, sticky=W, pady=2)
            self.cat_port_var = StringVar(value=self.config.cat_port)
            ttk.Combobox(frame, textvariable=self.cat_port_var, values=ports, width=15).grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            Label(frame, text="CAT Baud:").grid(row=row, column=0, sticky=W, pady=2)
            self.cat_baud_var = IntVar(value=self.config.cat_baud)
            ttk.Combobox(frame, textvariable=self.cat_baud_var, values=[4800, 9600, 19200, 38400, 57600, 115200], width=15).grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            Label(frame, text="Rig Type:").grid(row=row, column=0, sticky=W, pady=2)
            self.cat_rig_var = StringVar(value=self.config.cat_rig)
            ttk.Combobox(frame, textvariable=self.cat_rig_var, values=["", "FLEX", "ICOM7300", "ICOM7610"], width=15).grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            # Buttons
            btn_frame = Frame(frame)
            btn_frame.grid(row=row, column=0, columnspan=3, pady=10)

            Button(btn_frame, text="Save", command=self._save, width=10).pack(side='left', padx=5)
            Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side='left', padx=5)

        def _refresh_ports(self):
            ports = list_serial_ports()
            if not ports:
                ports = ["No ports found"]
            self.port_menu['values'] = ports

        def _save(self):
            self.config.port = self.port_var.get()
            self.config.method = self.method_var.get()
            self.config.wpm = self.wpm_var.get()
            self.config.ptt_enabled = bool(self.ptt_var.get())
            self.config.ptt_line = self.ptt_line_var.get()
            self.config.ptt_lead = self.ptt_lead_var.get()
            self.config.ptt_tail = self.ptt_tail_var.get()
            self.config.cat_enabled = bool(self.cat_var.get())
            self.config.cat_port = self.cat_port_var.get()
            try:
                self.config.cat_baud = int(self.cat_baud_var.get())
            except:
                self.config.cat_baud = 9600
            self.config.cat_rig = self.cat_rig_var.get()

            self.result = self.config

            if self.on_save:
                self.on_save(self.config)

            self.dialog.destroy()

        def _cancel(self):
            self.result = None
            self.dialog.destroy()

        def _center_window(self):
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f'+{x}+{y}')


    class CWMacroEditorDialog:
        """Editor dialog for CW macros."""

        def __init__(self, parent, macro_manager: CWMacroManager, on_save: Optional[Callable[[Dict[str, str]], None]] = None):
            self.parent = parent
            self.macro_manager = macro_manager
            self.on_save = on_save
            self.result = None
            self.entries = {}

            self.dialog = Toplevel(parent)
            self.dialog.title("CW Macros")
            self.dialog.transient(parent)
            self.dialog.grab_set()

            self._create_widgets()
            self._center_window()

        def _create_widgets(self):
            frame = Frame(self.dialog, padx=10, pady=10)
            frame.pack(fill='both', expand=True)

            # Instructions
            Label(frame, text="Available variables: {MYCALL}, {CALL}, {RST}, {CLASS}, {SECT}, {NAME}").grid(
                row=0, column=0, columnspan=2, sticky=W, pady=(0, 10))

            # Macro entries
            for i in range(1, 13):
                key = f'F{i}'
                Label(frame, text=f"{key}:").grid(row=i, column=0, sticky=W, pady=2)
                entry = Entry(frame, width=40)
                entry.insert(0, self.macro_manager.get_macro(key))
                entry.grid(row=i, column=1, sticky=EW, pady=2)
                self.entries[key] = entry

            frame.grid_columnconfigure(1, weight=1)

            # Buttons
            btn_frame = Frame(frame)
            btn_frame.grid(row=14, column=0, columnspan=2, pady=10)

            Button(btn_frame, text="Save", command=self._save, width=10).pack(side='left', padx=5)
            Button(btn_frame, text="Reset Defaults", command=self._reset, width=12).pack(side='left', padx=5)
            Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side='left', padx=5)

        def _save(self):
            macros = {}
            for key, entry in self.entries.items():
                macros[key] = entry.get()
                self.macro_manager.set_macro(key, entry.get())

            self.result = macros

            if self.on_save:
                self.on_save(macros)

            self.dialog.destroy()

        def _reset(self):
            for key, entry in self.entries.items():
                entry.delete(0, END)
                entry.insert(0, CWMacroManager.DEFAULT_MACROS.get(key, ''))

        def _cancel(self):
            self.result = None
            self.dialog.destroy()

        def _center_window(self):
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f'+{x}+{y}')

except ImportError:
    TKINTER_AVAILABLE = False
    CWSettingsDialog = None
    CWMacroEditorDialog = None
