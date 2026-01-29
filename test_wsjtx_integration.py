"""Tests for WSJT-X and JS8Call integration module."""

import struct
import unittest
from datetime import datetime, timezone
from wsjtx_integration import (
    QDataStreamParser, WSJTXMessage, WSJTXConfig,
    HeartbeatMessage, StatusMessage, DecodeMessage,
    QSOLoggedMessage, CloseMessage, LoggedADIFMessage,
    freq_to_band, parse_exchange,
    JS8CallConfig,
)


def _build_header(msg_type, client_id="WSJT-X"):
    """Build a WSJT-X packet header."""
    buf = struct.pack('>I', 0xADBCCBDA)  # magic
    buf += struct.pack('>I', 2)  # schema
    buf += struct.pack('>I', msg_type)
    buf += _pack_utf8(client_id)
    return buf


def _pack_utf8(s):
    b = s.encode('utf-8')
    return struct.pack('>I', len(b)) + b


def _pack_qdatetime(dt):
    """Pack a datetime as Qt QDateTime (julian day int64 + ms uint32 + timespec uint8)."""
    # Julian day for a date
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    ms = (dt.hour * 3600 + dt.minute * 60 + dt.second) * 1000
    return struct.pack('>q', jdn) + struct.pack('>I', ms) + struct.pack('>B', 2)  # UTC


class TestQDataStreamParser(unittest.TestCase):

    def test_read_quint32(self):
        p = QDataStreamParser(struct.pack('>I', 42))
        self.assertEqual(p.read_quint32(), 42)

    def test_read_qint32(self):
        p = QDataStreamParser(struct.pack('>i', -1))
        self.assertEqual(p.read_qint32(), -1)

    def test_read_quint64(self):
        p = QDataStreamParser(struct.pack('>Q', 14074000))
        self.assertEqual(p.read_quint64(), 14074000)

    def test_read_double(self):
        p = QDataStreamParser(struct.pack('>d', 3.14))
        self.assertAlmostEqual(p.read_double(), 3.14)

    def test_read_bool(self):
        p = QDataStreamParser(struct.pack('>?', True))
        self.assertTrue(p.read_bool())

    def test_read_utf8(self):
        s = "WSJT-X"
        data = _pack_utf8(s)
        p = QDataStreamParser(data)
        self.assertEqual(p.read_utf8(), s)

    def test_read_utf8_null(self):
        data = struct.pack('>I', 0xFFFFFFFF)
        p = QDataStreamParser(data)
        self.assertEqual(p.read_utf8(), "")

    def test_read_qdatetime(self):
        dt = datetime(2025, 6, 28, 18, 30, 0, tzinfo=timezone.utc)
        data = _pack_qdatetime(dt)
        p = QDataStreamParser(data)
        result = p.read_qdatetime()
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 28)
        self.assertEqual(result.hour, 18)
        self.assertEqual(result.minute, 30)

    def test_buffer_underrun(self):
        p = QDataStreamParser(b'\x00')
        with self.assertRaises(ValueError):
            p.read_quint32()


class TestFreqToBand(unittest.TestCase):

    def test_all_bands(self):
        self.assertEqual(freq_to_band(1850000), "160d")
        self.assertEqual(freq_to_band(3573000), "80d")
        self.assertEqual(freq_to_band(7074000), "40d")
        self.assertEqual(freq_to_band(14074000), "20d")
        self.assertEqual(freq_to_band(21074000), "15d")
        self.assertEqual(freq_to_band(28074000), "10d")
        self.assertEqual(freq_to_band(50313000), "6d")
        self.assertEqual(freq_to_band(144174000), "2d")
        self.assertEqual(freq_to_band(432065000), "220d")

    def test_band_boundaries(self):
        self.assertEqual(freq_to_band(14000000), "20d")
        self.assertEqual(freq_to_band(14350000), "20d")
        self.assertIsNone(freq_to_band(13999999))
        self.assertIsNone(freq_to_band(14350001))

    def test_unknown_freq(self):
        self.assertIsNone(freq_to_band(10000000))
        self.assertIsNone(freq_to_band(0))


class TestParseExchange(unittest.TestCase):

    def test_standard(self):
        self.assertEqual(parse_exchange("2A NH"), ("2A", "NH"))

    def test_three_letter_section(self):
        self.assertEqual(parse_exchange("3F WMA"), ("3F", "WMA"))

    def test_lowercase(self):
        self.assertEqual(parse_exchange("2a nh"), ("2A", "NH"))

    def test_with_extra_text(self):
        self.assertEqual(parse_exchange("R 2A NH"), ("2A", "NH"))

    def test_empty(self):
        self.assertIsNone(parse_exchange(""))
        self.assertIsNone(parse_exchange(None))

    def test_invalid(self):
        self.assertIsNone(parse_exchange("hello"))
        self.assertIsNone(parse_exchange("2G NH"))  # G not valid class letter


class TestMessageParsing(unittest.TestCase):

    def test_heartbeat(self):
        buf = _build_header(0)
        buf += struct.pack('>I', 3)  # max schema
        buf += _pack_utf8("2.6.1")  # version
        buf += _pack_utf8("abc123")  # revision
        msg = WSJTXMessage.parse(buf)
        self.assertIsInstance(msg, HeartbeatMessage)
        self.assertEqual(msg.version, "2.6.1")
        self.assertEqual(msg.client_id, "WSJT-X")

    def test_close(self):
        buf = _build_header(6, "WSJT-X")
        msg = WSJTXMessage.parse(buf)
        self.assertIsInstance(msg, CloseMessage)
        self.assertEqual(msg.client_id, "WSJT-X")

    def test_logged_adif(self):
        buf = _build_header(12)
        buf += _pack_utf8("<call:5>W1ABC <band:3>20m")
        msg = WSJTXMessage.parse(buf)
        self.assertIsInstance(msg, LoggedADIFMessage)
        self.assertIn("W1ABC", msg.adif_text)

    def test_qso_logged(self):
        dt = datetime(2025, 6, 28, 18, 30, 0, tzinfo=timezone.utc)
        buf = _build_header(5)
        buf += _pack_qdatetime(dt)   # date_time_off
        buf += _pack_utf8("W1ABC")   # dx_call
        buf += _pack_utf8("FN42")    # dx_grid
        buf += struct.pack('>Q', 14074000)  # tx_freq
        buf += _pack_utf8("FT8")     # mode
        buf += _pack_utf8("-10")     # report_sent
        buf += _pack_utf8("-15")     # report_recv
        buf += _pack_utf8("")        # tx_power
        buf += _pack_utf8("")        # comments
        buf += _pack_utf8("")        # name
        buf += _pack_qdatetime(dt)   # date_time_on
        buf += _pack_utf8("")        # operator_call
        buf += _pack_utf8("K2DEF")   # my_call
        buf += _pack_utf8("FN31")    # my_grid
        buf += _pack_utf8("2A EMA")  # exchange_sent
        buf += _pack_utf8("3F NH")   # exchange_recv
        msg = WSJTXMessage.parse(buf)
        self.assertIsInstance(msg, QSOLoggedMessage)
        self.assertEqual(msg.dx_call, "W1ABC")
        self.assertEqual(msg.tx_freq, 14074000)
        self.assertEqual(msg.exchange_recv, "3F NH")

    def test_invalid_magic(self):
        buf = struct.pack('>I', 0x12345678) + struct.pack('>I', 2) + struct.pack('>I', 0)
        msg = WSJTXMessage.parse(buf)
        self.assertIsNone(msg)

    def test_unknown_type(self):
        buf = _build_header(99)
        msg = WSJTXMessage.parse(buf)
        self.assertIsNone(msg)

    def test_status_message(self):
        buf = _build_header(1)
        buf += struct.pack('>Q', 14074000)  # dial_freq
        buf += _pack_utf8("FT8")    # mode
        buf += _pack_utf8("W1ABC")  # dx_call
        buf += _pack_utf8("-15")    # report
        buf += _pack_utf8("FT8")    # tx_mode
        buf += struct.pack('>?', True)   # tx_enabled
        buf += struct.pack('>?', False)  # transmitting
        buf += struct.pack('>?', True)   # decoding
        buf += struct.pack('>I', 1500)   # rx_df
        buf += struct.pack('>I', 1500)   # tx_df
        buf += _pack_utf8("K2DEF")  # de_call
        buf += _pack_utf8("FN31")   # de_grid
        buf += _pack_utf8("FN42")   # dx_grid
        buf += struct.pack('>?', False)  # tx_watchdog
        buf += _pack_utf8("")       # sub_mode
        buf += struct.pack('>?', False)  # fast_mode
        buf += struct.pack('>B', 0)      # special_op
        buf += struct.pack('>I', 0)      # freq_tolerance
        buf += struct.pack('>I', 15)     # tr_period
        buf += _pack_utf8("Default")    # config_name
        msg = WSJTXMessage.parse(buf)
        self.assertIsInstance(msg, StatusMessage)
        self.assertEqual(msg.dial_freq, 14074000)
        self.assertEqual(msg.mode, "FT8")


class TestWSJTXConfig(unittest.TestCase):

    def test_defaults(self):
        c = WSJTXConfig()
        self.assertFalse(c.enabled)
        self.assertEqual(c.udp_port, 2237)
        self.assertEqual(c.udp_ip, "127.0.0.1")
        self.assertTrue(c.auto_log)
        self.assertTrue(c.auto_band)


class TestJS8CallConfig(unittest.TestCase):

    def test_defaults(self):
        c = JS8CallConfig()
        self.assertFalse(c.enabled)
        self.assertEqual(c.udp_port, 2442)
        self.assertEqual(c.udp_ip, "127.0.0.1")
        self.assertTrue(c.auto_log)
        self.assertTrue(c.auto_band)


if __name__ == '__main__':
    unittest.main()
