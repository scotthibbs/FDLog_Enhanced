"""Tests for WSJT-X integration helpers (wsjtx_integration.py).

freq_to_band() and parse_exchange() are shared by the WSJT-X, JS8Call,
fldigi, N3FJP, and rigctld integrations — a regression here breaks all five.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wsjtx_integration import WSJTXConfig, freq_to_band, parse_exchange


class TestFreqToBand:
    def test_common_bands(self):
        assert freq_to_band(1840000) == "160d"
        assert freq_to_band(3573000) == "80d"
        assert freq_to_band(7074000) == "40d"
        assert freq_to_band(14074000) == "20d"
        assert freq_to_band(21074000) == "15d"
        assert freq_to_band(28074000) == "10d"
        assert freq_to_band(50313000) == "6d"
        assert freq_to_band(144174000) == "2d"

    def test_band_edges_inclusive(self):
        assert freq_to_band(7000000) == "40d"
        assert freq_to_band(7300000) == "40d"

    def test_out_of_band(self):
        assert freq_to_band(7300001) is None
        assert freq_to_band(6999999) is None
        assert freq_to_band(0) is None


class TestParseExchange:
    def test_standard_exchange(self):
        assert parse_exchange("3A CT") == ("3A", "CT")

    def test_lowercase_normalized(self):
        assert parse_exchange("3a ct") == ("3A", "CT")

    def test_three_letter_section(self):
        assert parse_exchange("2F EMA") == ("2F", "EMA")

    def test_multi_digit_class(self):
        assert parse_exchange("25A STX") == ("25A", "STX")

    def test_embedded_in_report(self):
        """Exchange may be embedded in a longer report string."""
        assert parse_exchange("R 3A IN") == ("3A", "IN")

    def test_empty_and_none(self):
        assert parse_exchange("") is None
        assert parse_exchange(None) is None

    def test_no_exchange_present(self):
        assert parse_exchange("just some text") is None


class TestConfigDefaults:
    def test_defaults(self):
        cfg = WSJTXConfig()
        assert cfg.udp_port == 2237      # WSJT-X default; MSHV uses the same
        assert cfg.udp_ip == "127.0.0.1"
        assert cfg.enabled is False
        assert cfg.auto_log is True
        assert cfg.auto_band is True
