"""
Voice Keying Interface for FDLog_Enhanced
Text-to-Speech and recorded audio voice keyer for Phone mode.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List
from pathlib import Path

# Try to import pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Try to import pyserial (for PTT control)
try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False

# Try to import recording support
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    RECORDING_AVAILABLE = True
except ImportError:
    RECORDING_AVAILABLE = False

RECORDINGS_DIR = Path.home() / ".fdlog_voice_recordings"


def list_serial_ports() -> List[str]:
    """Get list of available serial ports."""
    if not PYSERIAL_AVAILABLE:
        return []
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(port.device)
    return sorted(ports)


@dataclass
class VoiceConfig:
    """Voice keyer configuration settings."""
    speed: int = 150       # TTS speech rate (words per minute)
    volume: float = 1.0    # TTS volume (0.0 - 1.0)
    voice_id: str = ""     # TTS voice identifier (empty = auto-select)

    # PTT settings
    ptt_enabled: bool = False
    ptt_port: str = ""      # COM port for PTT (empty = use CW port)
    ptt_line: str = "RTS"   # RTS or DTR
    ptt_lead: int = 100     # ms before audio starts
    ptt_tail: int = 100     # ms after audio ends
    use_cw_port: bool = True  # True = reuse CW serial port settings

    def copy(self) -> 'VoiceConfig':
        return VoiceConfig(
            speed=self.speed, volume=self.volume, voice_id=self.voice_id,
            ptt_enabled=self.ptt_enabled, ptt_port=self.ptt_port,
            ptt_line=self.ptt_line, ptt_lead=self.ptt_lead,
            ptt_tail=self.ptt_tail, use_cw_port=self.use_cw_port
        )


class VoiceMacroManager:
    """Manages voice macros with variable substitution."""

    DEFAULT_MACROS = {
        'F1': 'CQ Field Day {MYCALL} {MYCALL}',
        'F2': '{CALL} you are five nine {CLASS} {SECT}',
        'F3': 'Thank you, {MYCALL}',
        'F4': '{CALL}',
        'F5': '{MYCALL}',
        'F6': 'CQ CQ Field Day, {MYCALL}',
        'F7': 'Roger, five nine {CLASS} {SECT}',
        'F8': 'Please copy, five nine {CLASS} {SECT}',
        'F9': 'seventy three',
        'F10': 'QRZ?',
        'F11': 'Again?',
        'F12': 'Thank you, QRZ? {MYCALL}',
    }

    DEFAULT_MODES = {f'F{i}': 'tts' for i in range(1, 13)}

    def __init__(self, get_variable_func: Optional[Callable[[str], str]] = None):
        self.macros = dict(self.DEFAULT_MACROS)
        self.modes = dict(self.DEFAULT_MODES)  # "tts" or "rec" per slot
        self.get_variable = get_variable_func or (lambda x: f"{{{x}}}")

    def set_macro(self, key: str, value: str) -> None:
        self.macros[key.upper()] = value

    def get_macro(self, key: str) -> str:
        return self.macros.get(key.upper(), '')

    def get_mode(self, key: str) -> str:
        return self.modes.get(key.upper(), 'tts')

    def set_mode(self, key: str, mode: str) -> None:
        self.modes[key.upper()] = mode

    def expand_macro(self, key: str) -> str:
        raw = self.get_macro(key)
        return self.substitute_variables(raw)

    def substitute_variables(self, text: str) -> str:
        import re
        def replace_var(match):
            var_name = match.group(1)
            return self.get_variable(var_name)
        return re.sub(r'\{(\w+)\}', replace_var, text)

    def get_all_macros(self) -> Dict[str, str]:
        return dict(self.macros)

    def load_from_dict(self, data: Dict[str, str]) -> None:
        for key, value in data.items():
            if key.upper().startswith('F') and key[1:].isdigit():
                self.macros[key.upper()] = value

    def load_modes_from_dict(self, data: Dict[str, str]) -> None:
        for key, value in data.items():
            if key.upper().startswith('F') and key[1:].isdigit():
                self.modes[key.upper()] = value

    def to_dict(self) -> Dict[str, str]:
        return dict(self.macros)


class VoiceKeyer:
    """Voice keyer engine using TTS and/or recorded WAV files."""

    def __init__(self, config: VoiceConfig, root=None, status_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.root = root
        self.status_callback = status_callback
        self.macro_manager = VoiceMacroManager()
        self._playing = False
        self._aborted = False
        self._engine = None
        self._ptt_port: Optional['serial.Serial'] = None
        self._cw_ptt_func = None  # callback pair (on, off) to reuse CW port
        self.lock = threading.RLock()

        # Ensure recordings directory
        RECORDINGS_DIR.mkdir(exist_ok=True)

        # Find preferred voice on init
        if PYTTSX3_AVAILABLE and not config.voice_id:
            config.voice_id = self._find_female_voice_id()

    def _find_female_voice_id(self) -> str:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice_id = ""
            for voice in voices:
                if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                    voice_id = voice.id
                    break
                elif any(name in voice.name.lower() for name in ['zira', 'hazel', 'samantha', 'victoria', 'karen']):
                    voice_id = voice.id
                    break
            if not voice_id and len(voices) > 1:
                voice_id = voices[1].id
            engine.stop()
            del engine
            return voice_id
        except Exception:
            return ""

    def _create_engine(self):
        engine = pyttsx3.init()
        if self.config.voice_id:
            engine.setProperty('voice', self.config.voice_id)
        engine.setProperty('rate', self.config.speed)
        engine.setProperty('volume', self.config.volume)
        return engine

    def set_variable_getter(self, func: Callable[[str], str]) -> None:
        self.macro_manager.get_variable = func

    def set_cw_ptt(self, ptt_on_func, ptt_off_func):
        """Set callbacks to reuse CW port for PTT."""
        self._cw_ptt_func = (ptt_on_func, ptt_off_func)

    def _ptt_on(self) -> None:
        """Key the transmitter."""
        if not self.config.ptt_enabled:
            return
        if self.config.use_cw_port and self._cw_ptt_func:
            try:
                self._cw_ptt_func[0]()
            except Exception as e:
                print(f"Voice: CW PTT on error: {e}")
            return
        # Use own serial port
        if not PYSERIAL_AVAILABLE or not self.config.ptt_port:
            return
        try:
            if not self._ptt_port or not self._ptt_port.is_open:
                self._ptt_port = serial.Serial()
                self._ptt_port.port = self.config.ptt_port
                self._ptt_port.baudrate = 9600
                self._ptt_port.timeout = 0.1
                self._ptt_port.open()
                self._ptt_port.dtr = False
                self._ptt_port.rts = False
            if self.config.ptt_line == "DTR":
                self._ptt_port.dtr = True
            else:
                self._ptt_port.rts = True
        except Exception as e:
            print(f"Voice: PTT on error: {e}")

    def _ptt_off(self) -> None:
        """Unkey the transmitter."""
        if not self.config.ptt_enabled:
            return
        if self.config.use_cw_port and self._cw_ptt_func:
            try:
                self._cw_ptt_func[1]()
            except Exception as e:
                print(f"Voice: CW PTT off error: {e}")
            return
        if self._ptt_port and self._ptt_port.is_open:
            try:
                if self.config.ptt_line == "DTR":
                    self._ptt_port.dtr = False
                else:
                    self._ptt_port.rts = False
            except Exception as e:
                print(f"Voice: PTT off error: {e}")

    def close_ptt_port(self) -> None:
        """Close the dedicated PTT serial port."""
        if self._ptt_port and self._ptt_port.is_open:
            try:
                self._ptt_port.dtr = False
                self._ptt_port.rts = False
                self._ptt_port.close()
            except Exception:
                pass
            self._ptt_port = None

    def is_playing(self) -> bool:
        return self._playing

    def play_macro(self, key: str) -> None:
        """Play voice macro for given F-key."""
        mode = self.macro_manager.get_mode(key)
        if mode == "rec" and RECORDING_AVAILABLE:
            self._play_recording(key)
        else:
            text = self.macro_manager.expand_macro(key)
            if text:
                self._play_tts(text, key)

    def _play_tts(self, text: str, label: str = "") -> None:
        if not PYTTSX3_AVAILABLE:
            self._update_status("pyttsx3 not installed")
            return
        if self._playing:
            return

        def speak():
            try:
                self._playing = True
                self._aborted = False
                self._update_status(f"Speaking: {label or text}")
                # PTT lead-in
                self._ptt_on()
                if self.config.ptt_enabled and self.config.ptt_lead > 0:
                    time.sleep(self.config.ptt_lead / 1000.0)
                engine = self._create_engine()
                self._engine = engine
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                if not self._aborted:
                    print(f"Voice: Error speaking: {e}")
            finally:
                try:
                    if self._engine:
                        self._engine.stop()
                        self._engine = None
                except Exception:
                    pass
                # PTT tail
                if self.config.ptt_enabled and self.config.ptt_tail > 0:
                    time.sleep(self.config.ptt_tail / 1000.0)
                self._ptt_off()
                self._playing = False
                if not self._aborted:
                    self._update_status("Ready")

        thread = threading.Thread(target=speak, daemon=True)
        thread.start()

    def _recording_path(self, key: str) -> Path:
        return RECORDINGS_DIR / f"{key}.wav"

    def _has_recording(self, key: str) -> bool:
        return self._recording_path(key).exists()

    def _play_recording(self, key: str) -> None:
        if not RECORDING_AVAILABLE:
            self._update_status("sounddevice not installed")
            return
        path = self._recording_path(key)
        if not path.exists():
            self._update_status(f"No recording for {key}")
            return
        if self._playing:
            return

        def play():
            try:
                self._playing = True
                self._aborted = False
                self._update_status(f"Playing: {key}")
                # PTT lead-in
                self._ptt_on()
                if self.config.ptt_enabled and self.config.ptt_lead > 0:
                    time.sleep(self.config.ptt_lead / 1000.0)
                data, samplerate = sf.read(str(path))
                sd.play(data, samplerate)
                sd.wait()
            except Exception as e:
                print(f"Voice: Error playing recording: {e}")
            finally:
                # PTT tail
                if self.config.ptt_enabled and self.config.ptt_tail > 0:
                    time.sleep(self.config.ptt_tail / 1000.0)
                self._ptt_off()
                self._playing = False
                if not self._aborted:
                    self._update_status("Ready")

        thread = threading.Thread(target=play, daemon=True)
        thread.start()

    def stop(self) -> None:
        """Stop current playback."""
        self._aborted = True
        self._playing = False
        # Unkey PTT immediately
        self._ptt_off()
        # Stop TTS engine if running
        if self._engine:
            try:
                self._engine.endLoop()
            except Exception:
                pass
            try:
                self._engine.stop()
            except Exception:
                pass
            self._engine = None
        # Stop recording playback
        if RECORDING_AVAILABLE:
            try:
                sd.stop()
            except Exception:
                pass
        self._update_status("Stopped")
        if self.root:
            self.root.after(2000, lambda: self._update_status("Ready"))

    def get_available_voices(self):
        """Return list of (id, name) tuples for available TTS voices."""
        if not PYTTSX3_AVAILABLE:
            return []
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            result = [(v.id, v.name) for v in voices]
            engine.stop()
            del engine
            return result
        except Exception:
            return []

    def _update_status(self, status: str) -> None:
        if self.status_callback:
            if self.root:
                self.root.after(0, lambda: self.status_callback(status))
            else:
                self.status_callback(status)


# Tkinter dialogs
try:
    from tkinter import (Toplevel, Frame, Label, Entry, Button, StringVar, IntVar, DoubleVar,
                         W, E, EW, NSEW, END, HORIZONTAL)
    from tkinter import ttk, messagebox
    import tkinter as tk

    class VoiceSettingsDialog:
        """Settings dialog for voice configuration."""

        def __init__(self, parent, config: VoiceConfig, keyer: VoiceKeyer,
                     on_save: Optional[Callable[[VoiceConfig], None]] = None):
            self.parent = parent
            self.config = config.copy()
            self.keyer = keyer
            self.on_save = on_save

            self.dialog = Toplevel(parent)
            self.dialog.title("Voice Keyer Settings")
            self.dialog.transient(parent)
            self.dialog.grab_set()

            self._create_widgets()
            self._center_window()

        def _create_widgets(self):
            frame = Frame(self.dialog, padx=10, pady=10)
            frame.pack(fill='both', expand=True)

            row = 0

            # Speed
            Label(frame, text="Speech Rate:").grid(row=row, column=0, sticky=W, pady=2)
            self.speed_var = IntVar(value=self.config.speed)
            tk.Scale(frame, from_=80, to=250, orient=HORIZONTAL, variable=self.speed_var,
                     length=200).grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            # Volume
            Label(frame, text="Volume:").grid(row=row, column=0, sticky=W, pady=2)
            self.volume_var = DoubleVar(value=self.config.volume)
            tk.Scale(frame, from_=0.0, to=1.0, resolution=0.1, orient=HORIZONTAL,
                     variable=self.volume_var, length=200).grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            # Voice selection
            Label(frame, text="Voice:").grid(row=row, column=0, sticky=W, pady=2)
            voices = self.keyer.get_available_voices()
            self.voice_names = [name for _, name in voices]
            self.voice_ids = [vid for vid, _ in voices]
            current_name = ""
            if self.config.voice_id in self.voice_ids:
                idx = self.voice_ids.index(self.config.voice_id)
                current_name = self.voice_names[idx]
            elif self.voice_names:
                current_name = self.voice_names[0]
            self.voice_var = StringVar(value=current_name)
            if self.voice_names:
                self.voice_combo = ttk.Combobox(frame, textvariable=self.voice_var,
                                                values=self.voice_names, width=30, state='readonly')
                self.voice_combo.grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            # Separator
            ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=EW, pady=10)
            row += 1

            # PTT settings
            Label(frame, text="PTT Control", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky=W, pady=2)
            row += 1

            self.ptt_var = IntVar(value=1 if self.config.ptt_enabled else 0)
            tk.Checkbutton(frame, text="Enable PTT", variable=self.ptt_var,
                           command=self._update_ptt_state).grid(row=row, column=0, columnspan=2, sticky=W, pady=2)
            row += 1

            self.use_cw_var = IntVar(value=1 if self.config.use_cw_port else 0)
            tk.Checkbutton(frame, text="Use CW port for PTT", variable=self.use_cw_var,
                           command=self._update_ptt_state).grid(row=row, column=0, columnspan=2, sticky=W, pady=2)
            row += 1

            Label(frame, text="PTT Port:").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_port_var = StringVar(value=self.config.ptt_port)
            ports = list_serial_ports()
            if not ports:
                ports = ["No ports found"]
            if self.config.ptt_port and self.config.ptt_port not in ports:
                ports.insert(0, self.config.ptt_port)
            self.ptt_port_combo = ttk.Combobox(frame, textvariable=self.ptt_port_var, values=ports, width=15)
            self.ptt_port_combo.grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            Label(frame, text="PTT Line:").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_line_var = StringVar(value=self.config.ptt_line)
            ttk.Combobox(frame, textvariable=self.ptt_line_var, values=["RTS", "DTR"],
                         width=15, state='readonly').grid(row=row, column=1, sticky=EW, pady=2)
            row += 1

            Label(frame, text="PTT Lead-in (ms):").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_lead_var = IntVar(value=self.config.ptt_lead)
            tk.Spinbox(frame, from_=0, to=500, textvariable=self.ptt_lead_var, width=10).grid(row=row, column=1, sticky=W, pady=2)
            row += 1

            Label(frame, text="PTT Tail (ms):").grid(row=row, column=0, sticky=W, pady=2)
            self.ptt_tail_var = IntVar(value=self.config.ptt_tail)
            tk.Spinbox(frame, from_=0, to=500, textvariable=self.ptt_tail_var, width=10).grid(row=row, column=1, sticky=W, pady=2)
            row += 1

            self._update_ptt_state()

            # Separator
            ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=EW, pady=10)
            row += 1

            # Test button
            Button(frame, text="Test Voice", command=self._test).grid(row=row, column=0, columnspan=2, pady=5)
            row += 1

            # Buttons
            btn_frame = Frame(frame)
            btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
            Button(btn_frame, text="Save", command=self._save, width=10).pack(side='left', padx=5)
            Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side='left', padx=5)

        def _update_ptt_state(self):
            """Enable/disable PTT port controls based on checkbox state."""
            ptt_on = bool(self.ptt_var.get())
            use_cw = bool(self.use_cw_var.get())
            state = 'normal' if (ptt_on and not use_cw) else 'disabled'
            self.ptt_port_combo.config(state=state)

        def _test(self):
            """Test current voice settings."""
            if self.keyer.is_playing():
                return
            # Temporarily apply settings for test
            old_config = self.keyer.config.copy()
            self.keyer.config.speed = self.speed_var.get()
            self.keyer.config.volume = self.volume_var.get()
            if self.voice_var.get() in self.voice_names:
                idx = self.voice_names.index(self.voice_var.get())
                self.keyer.config.voice_id = self.voice_ids[idx]
            self.keyer._play_tts("CQ CQ Field Day, testing voice keyer.", "Test")
            # Restore after a delay (playback is threaded)
            self.dialog.after(100, lambda: setattr(self.keyer, 'config', old_config))

        def _save(self):
            self.config.speed = self.speed_var.get()
            self.config.volume = self.volume_var.get()
            if self.voice_var.get() in self.voice_names:
                idx = self.voice_names.index(self.voice_var.get())
                self.config.voice_id = self.voice_ids[idx]
            self.config.ptt_enabled = bool(self.ptt_var.get())
            self.config.use_cw_port = bool(self.use_cw_var.get())
            self.config.ptt_port = self.ptt_port_var.get()
            self.config.ptt_line = self.ptt_line_var.get()
            self.config.ptt_lead = self.ptt_lead_var.get()
            self.config.ptt_tail = self.ptt_tail_var.get()

            if self.on_save:
                self.on_save(self.config)
            self.dialog.destroy()

        def _cancel(self):
            self.dialog.destroy()

        def _center_window(self):
            self.dialog.update_idletasks()
            w = self.dialog.winfo_width()
            h = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
            self.dialog.geometry(f'+{x}+{y}')


    class VoiceMacroEditorDialog:
        """Editor dialog for voice macros with optional recording support."""

        def __init__(self, parent, macro_manager: VoiceMacroManager,
                     on_save: Optional[Callable[[Dict[str, str], Dict[str, str]], None]] = None):
            self.parent = parent
            self.macro_manager = macro_manager
            self.on_save = on_save
            self.entries = {}
            self.mode_vars = {}

            # Recording state
            self.is_recording = False
            self.recording_key = None
            self.recorded_data = []
            self._rec_stream = None
            self.record_buttons = {}
            self.rec_labels = {}

            self.dialog = Toplevel(parent)
            self.dialog.title("Voice Macros")
            self.dialog.transient(parent)
            self.dialog.grab_set()

            self._create_widgets()
            self._center_window()

        def _recording_path(self, key):
            return RECORDINGS_DIR / f"{key}.wav"

        def _has_recording(self, key):
            return self._recording_path(key).exists()

        def _recording_duration(self, key):
            path = self._recording_path(key)
            if not path.exists():
                return None
            try:
                info = sf.info(str(path))
                return info.duration
            except Exception:
                return None

        def _update_rec_label(self, key):
            if key not in self.rec_labels:
                return
            if self._has_recording(key):
                dur = self._recording_duration(key)
                if dur is not None:
                    self.rec_labels[key].config(text=f"Recorded ({dur:.1f}s)")
                else:
                    self.rec_labels[key].config(text="Recorded")
            else:
                self.rec_labels[key].config(text="No recording")

        def _create_widgets(self):
            frame = Frame(self.dialog, padx=10, pady=10)
            frame.pack(fill='both', expand=True)

            # Show variables with current values
            var_names = ['MYCALL', 'CALL', 'RST', 'CLASS', 'SECT', 'NAME']
            var_lines = []
            for vn in var_names:
                val = self.macro_manager.get_variable(vn)
                if val and val != f'{{{vn}}}':
                    var_lines.append(f"{{{vn}}} = {val}")
                else:
                    var_lines.append(f"{{{vn}}}")
            Label(frame, text="Variables:  " + "    ".join(var_lines), anchor=W).grid(
                row=0, column=0, columnspan=5, sticky=W, pady=(0, 10))

            for i in range(1, 13):
                key = f'F{i}'
                row = i

                Label(frame, text=f"{key}:").grid(row=row, column=0, sticky=W, pady=2)

                # Mode selector
                mode_var = StringVar(value=self.macro_manager.get_mode(key))
                self.mode_vars[key] = mode_var

                if RECORDING_AVAILABLE:
                    mode_frame = Frame(frame)
                    mode_frame.grid(row=row, column=1, sticky=W, pady=2)
                    tk.Radiobutton(mode_frame, text="TTS", variable=mode_var, value="tts").pack(side='left')
                    tk.Radiobutton(mode_frame, text="Rec", variable=mode_var, value="rec").pack(side='left')

                # Text entry (used for TTS mode)
                entry = Entry(frame, width=40)
                entry.insert(0, self.macro_manager.get_macro(key))
                entry.grid(row=row, column=2, sticky=EW, pady=2)
                self.entries[key] = entry

                # Record button and recording status label
                if RECORDING_AVAILABLE:
                    rec_btn = Button(frame, text="Rec", width=4,
                                     command=lambda k=key: self._toggle_recording(k))
                    rec_btn.grid(row=row, column=3, padx=2, pady=2)
                    self.record_buttons[key] = rec_btn

                    rec_label = Label(frame, text="", font=("Arial", 8), width=14, anchor=W)
                    rec_label.grid(row=row, column=4, padx=2, pady=2, sticky=W)
                    self.rec_labels[key] = rec_label
                    self._update_rec_label(key)

            frame.grid_columnconfigure(2, weight=1)

            # Note about recording support
            note_row = 14
            if not RECORDING_AVAILABLE:
                Label(frame, text="Install sounddevice + soundfile + numpy for recording support",
                      font=("Arial", 8), fg="gray").grid(row=note_row, column=0, columnspan=5, sticky=W, pady=(5, 0))
                note_row = 15

            # Buttons
            btn_frame = Frame(frame)
            btn_frame.grid(row=note_row, column=0, columnspan=5, pady=10)
            Button(btn_frame, text="Save", command=self._save, width=10).pack(side='left', padx=5)
            Button(btn_frame, text="Reset Defaults", command=self._reset, width=12).pack(side='left', padx=5)
            Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side='left', padx=5)

        def _toggle_recording(self, key):
            if not RECORDING_AVAILABLE:
                return
            if self.is_recording:
                if self.recording_key == key:
                    self._stop_recording()
                return
            self.is_recording = True
            self.recording_key = key
            self.recorded_data = []
            self.record_buttons[key].config(text="Stop", bg="#f44336")

            samplerate = 44100
            def callback(indata, frames, time_info, status):
                self.recorded_data.append(indata.copy())

            self._rec_stream = sd.InputStream(samplerate=samplerate, channels=1, callback=callback)
            self._rec_stream.start()

        def _stop_recording(self):
            if not self.is_recording:
                return
            key = self.recording_key
            self._rec_stream.stop()
            self._rec_stream.close()

            if self.recorded_data:
                data = np.concatenate(self.recorded_data, axis=0)
                path = RECORDINGS_DIR / f"{key}.wav"
                RECORDINGS_DIR.mkdir(exist_ok=True)
                sf.write(str(path), data, 44100)

            self.is_recording = False
            self.recording_key = None
            self.recorded_data = []
            try:
                self.record_buttons[key].config(text="Rec", bg="SystemButtonFace")
            except tk.TclError:
                self.record_buttons[key].config(text="Rec")
            self._update_rec_label(key)

        def _save(self):
            macros = {}
            modes = {}
            for key, entry in self.entries.items():
                macros[key] = entry.get()
                self.macro_manager.set_macro(key, entry.get())
            for key, mode_var in self.mode_vars.items():
                modes[key] = mode_var.get()
                self.macro_manager.set_mode(key, mode_var.get())

            if self.on_save:
                self.on_save(macros, modes)
            self.dialog.destroy()

        def _reset(self):
            for key, entry in self.entries.items():
                entry.delete(0, END)
                entry.insert(0, VoiceMacroManager.DEFAULT_MACROS.get(key, ''))
                if key in self.mode_vars:
                    self.mode_vars[key].set('tts')

        def _cancel(self):
            if self.is_recording:
                self._stop_recording()
            self.dialog.destroy()

        def _center_window(self):
            self.dialog.update_idletasks()
            w = self.dialog.winfo_width()
            h = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
            self.dialog.geometry(f'+{x}+{y}')

except ImportError:
    VoiceSettingsDialog = None
    VoiceMacroEditorDialog = None
