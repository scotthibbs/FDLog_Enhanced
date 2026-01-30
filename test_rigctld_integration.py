"""Unit tests for rigctld integration."""

import unittest
from rigctld_integration import (
    parse_freq_response,
    parse_mode_response,
    build_set_freq_command,
    build_set_mode_command,
    rigctld_mode_to_suffix,
    RigctldConfig,
    BAND_FREQ_MAP,
)


class TestParseFreqResponse(unittest.TestCase):
    def test_valid_frequency(self):
        self.assertEqual(parse_freq_response("14074000\n"), 14074000)

    def test_valid_frequency_no_newline(self):
        self.assertEqual(parse_freq_response("7074000"), 7074000)

    def test_error_response(self):
        self.assertIsNone(parse_freq_response("RPRT -1\n"))

    def test_empty(self):
        self.assertIsNone(parse_freq_response(""))

    def test_garbage(self):
        self.assertIsNone(parse_freq_response("abc\n"))


class TestParseModeResponse(unittest.TestCase):
    def test_usb(self):
        result = parse_mode_response("USB\n2400\n")
        self.assertEqual(result, ("USB", 2400))

    def test_cw(self):
        result = parse_mode_response("CW\n500\n")
        self.assertEqual(result, ("CW", 500))

    def test_error(self):
        self.assertIsNone(parse_mode_response("RPRT -1\n"))

    def test_empty(self):
        self.assertIsNone(parse_mode_response(""))

    def test_mode_only(self):
        result = parse_mode_response("LSB\n")
        self.assertEqual(result, ("LSB", 0))


class TestBuildCommands(unittest.TestCase):
    def test_set_freq(self):
        self.assertEqual(build_set_freq_command(14250000), "F 14250000\n")

    def test_set_mode(self):
        self.assertEqual(build_set_mode_command("USB", 2400), "M USB 2400\n")

    def test_set_mode_zero_passband(self):
        self.assertEqual(build_set_mode_command("CW", 0), "M CW 0\n")


class TestModeMapping(unittest.TestCase):
    def test_phone_modes(self):
        for mode in ("USB", "LSB", "AM", "FM"):
            self.assertEqual(rigctld_mode_to_suffix(mode), "p")

    def test_cw_modes(self):
        for mode in ("CW", "CWR"):
            self.assertEqual(rigctld_mode_to_suffix(mode), "c")

    def test_digital_modes(self):
        for mode in ("RTTY", "RTTYR", "PKTUSB", "PKTLSB", "DATA"):
            self.assertEqual(rigctld_mode_to_suffix(mode), "d")

    def test_unknown_mode_defaults_phone(self):
        self.assertEqual(rigctld_mode_to_suffix("UNKNOWN"), "p")

    def test_case_insensitive(self):
        self.assertEqual(rigctld_mode_to_suffix("usb"), "p")
        self.assertEqual(rigctld_mode_to_suffix("cw"), "c")


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = RigctldConfig()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.host, "127.0.0.1")
        self.assertEqual(cfg.port, 4532)
        self.assertEqual(cfg.poll_interval, 2.0)
        self.assertTrue(cfg.auto_band)
        self.assertTrue(cfg.push_frequency)


class TestBandFreqMap(unittest.TestCase):
    def test_all_bands_have_entries(self):
        for suffix in ("c", "p", "d"):
            for band in ("160", "80", "40", "20", "15", "10", "6", "2", "220"):
                key = band + suffix
                self.assertIn(key, BAND_FREQ_MAP, f"Missing {key}")


if __name__ == "__main__":
    unittest.main()
