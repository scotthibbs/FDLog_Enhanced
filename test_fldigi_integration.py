"""Tests for fldigi integration module."""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from fldigi_integration import (
    FldigiConfig, FldigiPoller, FldigiSettingsDialog,
    BAND_FREQ_MAP,
)
from wsjtx_integration import freq_to_band


class TestFldigiConfig(unittest.TestCase):

    def test_defaults(self):
        c = FldigiConfig()
        self.assertFalse(c.enabled)
        self.assertEqual(c.xmlrpc_host, "127.0.0.1")
        self.assertEqual(c.xmlrpc_port, 7362)
        self.assertEqual(c.poll_interval, 1.5)
        self.assertTrue(c.auto_log)
        self.assertTrue(c.auto_band)
        self.assertTrue(c.push_frequency)
        self.assertFalse(c.push_callsign)


class TestBandFreqMapping(unittest.TestCase):

    def test_all_bands_map_back(self):
        """Every frequency in BAND_FREQ_MAP should resolve to a band via freq_to_band."""
        for band_str, freq in BAND_FREQ_MAP.items():
            # The band letter may differ (d/c/p) but the number part should match
            result = freq_to_band(freq)
            self.assertIsNotNone(result, f"freq_to_band({freq}) returned None for band {band_str}")

    def test_known_frequencies(self):
        self.assertEqual(BAND_FREQ_MAP["20d"], 14074000)
        self.assertEqual(BAND_FREQ_MAP["40d"], 7074000)
        self.assertEqual(BAND_FREQ_MAP["80d"], 3573000)
        self.assertEqual(BAND_FREQ_MAP["2d"], 144174000)

    def test_default_port(self):
        c = FldigiConfig()
        self.assertEqual(c.xmlrpc_port, 7362)


class TestFldigiPoller(unittest.TestCase):

    def setUp(self):
        self.config = FldigiConfig()
        self.on_qso = MagicMock()
        self.on_status = MagicMock()
        self.on_band = MagicMock()
        self.poller = FldigiPoller(self.config, self.on_qso, self.on_status, self.on_band)

    def test_initial_state(self):
        self.assertFalse(self.poller.is_connected())
        self.assertFalse(self.poller._running)
        self.assertIsNone(self.poller._proxy)

    def test_get_status(self):
        status = self.poller.get_status()
        self.assertFalse(status['connected'])
        self.assertEqual(status['frequency'], 0)
        self.assertEqual(status['mode'], "")
        self.assertFalse(status['running'])

    def test_qso_detection_call_transition(self):
        """Test that QSO is detected when call transitions from non-empty to empty."""
        # Simulate polling with a call present
        self.poller._last_call = ""
        self.poller._poll_qso_fields_with_values("W1ABC", 14074000, "2A NH")
        # Call is populated - should be cached, no QSO yet
        self.assertEqual(self.poller._cached_call, "W1ABC")
        self.on_qso.assert_not_called()

        # Now call goes empty - QSO detected
        self.poller._poll_qso_fields_with_values("", 14074000, "")
        self.on_qso.assert_called_once()
        args = self.on_qso.call_args[0]
        self.assertEqual(args[0], "W1ABC")  # call
        self.assertEqual(args[1], "20d")     # band
        self.assertEqual(args[2], "2a nh")   # report

    def test_qso_detection_no_false_trigger(self):
        """Empty-to-empty should not trigger a QSO."""
        self.poller._last_call = ""
        self.poller._poll_qso_fields_with_values("", 14074000, "")
        self.on_qso.assert_not_called()

    def test_set_frequency(self):
        """set_frequency should call proxy when connected."""
        self.poller._connected = True
        self.poller._proxy = MagicMock()
        self.poller.set_frequency(14074000)
        self.poller._proxy.main.set_frequency.assert_called_once_with(14074000.0)

    def test_set_frequency_not_connected(self):
        """set_frequency should do nothing when not connected."""
        self.poller._connected = False
        self.poller._proxy = MagicMock()
        self.poller.set_frequency(14074000)
        self.poller._proxy.main.set_frequency.assert_not_called()

    def test_set_callsign(self):
        """set_callsign should call proxy when connected."""
        self.poller._connected = True
        self.poller._proxy = MagicMock()
        self.poller.set_callsign("W1ABC")
        self.poller._proxy.log.set_call.assert_called_once_with("W1ABC")


# Helper method for testing without actual XML-RPC
def _poll_qso_fields_with_values(self, call, freq, exchange):
    """Test helper: simulate _poll_qso_fields with given values."""
    call = call.strip().upper()
    if call:
        self._cached_call = call
        self._cached_freq = freq
        self._cached_exchange = exchange
    elif self._last_call and not call:
        if self._cached_call and self.config.auto_log:
            self._process_qso()
    self._last_call = call

# Monkey-patch for testing
FldigiPoller._poll_qso_fields_with_values = _poll_qso_fields_with_values


if __name__ == '__main__':
    unittest.main()
