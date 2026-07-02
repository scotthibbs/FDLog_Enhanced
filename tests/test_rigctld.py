"""Tests for Hamlib rigctld protocol handling (rigctld_integration.py).

These import the real module — no mocks — so protocol changes break loudly.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rigctld_integration import (
    RigctldConfig, parse_freq_response, parse_mode_response,
    build_set_freq_command, build_set_mode_command,
    rigctld_mode_to_suffix, BAND_FREQ_MAP,
)
from wsjtx_integration import freq_to_band


class TestParseFreqResponse:
    def test_valid_frequency(self):
        assert parse_freq_response("14074000\n") == 14074000

    def test_whitespace(self):
        assert parse_freq_response("  7050000  \n") == 7050000

    def test_rprt_error(self):
        """rigctld reports errors as RPRT <code>."""
        assert parse_freq_response("RPRT -1\n") is None

    def test_garbage(self):
        assert parse_freq_response("not a number") is None

    def test_empty(self):
        assert parse_freq_response("") is None


class TestParseModeResponse:
    def test_mode_and_passband(self):
        assert parse_mode_response("USB\n2400\n") == ("USB", 2400)

    def test_mode_only(self):
        assert parse_mode_response("CW\n") == ("CW", 0)

    def test_bad_passband_defaults_zero(self):
        assert parse_mode_response("USB\nxyz\n") == ("USB", 0)

    def test_rprt_error(self):
        assert parse_mode_response("RPRT -5\n") is None

    def test_empty(self):
        assert parse_mode_response("") is None


class TestBuildCommands:
    def test_set_freq(self):
        assert build_set_freq_command(14074000) == "F 14074000\n"

    def test_set_mode(self):
        assert build_set_mode_command("USB") == "M USB 0\n"

    def test_set_mode_with_passband(self):
        assert build_set_mode_command("CW", 500) == "M CW 500\n"


class TestModeSuffix:
    def test_phone_modes(self):
        for m in ("USB", "LSB", "AM", "FM", "FMN", "WFM"):
            assert rigctld_mode_to_suffix(m) == 'p'

    def test_cw_modes(self):
        for m in ("CW", "CWR"):
            assert rigctld_mode_to_suffix(m) == 'c'

    def test_digital_modes(self):
        for m in ("RTTY", "RTTYR", "PKTUSB", "PKTLSB", "PKT", "DATAR",
                  "C4FM", "DV"):
            assert rigctld_mode_to_suffix(m) == 'd'

    def test_case_insensitive(self):
        assert rigctld_mode_to_suffix("usb") == 'p'

    def test_unknown_defaults_to_phone(self):
        assert rigctld_mode_to_suffix("MYSTERY") == 'p'


class TestConfigDefaults:
    def test_defaults(self):
        cfg = RigctldConfig()
        assert cfg.port == 4532          # rigctld default port
        assert cfg.host == "127.0.0.1"
        assert cfg.poll_interval == 2.0
        assert cfg.enabled is False
        assert cfg.auto_band is True
        assert cfg.push_frequency is True


class TestBandFreqMap:
    def test_band_freq_map_round_trip(self):
        """Every default frequency must land back in the same band."""
        for band, freq in BAND_FREQ_MAP.items():
            mapped = freq_to_band(freq)
            assert mapped is not None, "%s -> %d maps to no band" % (band, freq)
            assert mapped[:-1] == band[:-1], \
                "%s default freq %d maps to %s" % (band, freq, mapped)
