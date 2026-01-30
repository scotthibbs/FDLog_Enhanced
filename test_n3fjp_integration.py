"""Unit tests for N3FJP protocol parsing and message handling."""

import unittest
from n3fjp_integration import parse_messages, build_cmd, parse_adif, _mode_suffix


class TestParseMessages(unittest.TestCase):
    def test_single_simple_command(self):
        data = "<CMD>ENTER</CMD>\r\n"
        msgs = parse_messages(data)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['_type'], 'ENTER')

    def test_command_with_fields(self):
        data = "<CMD>UPDATE <TXTENTRYCALL>W1AW</TXTENTRYCALL><FREQ>14074000</FREQ></CMD>\r\n"
        msgs = parse_messages(data)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['_type'], 'UPDATE')
        self.assertEqual(msgs[0]['TXTENTRYCALL'], 'W1AW')
        self.assertEqual(msgs[0]['FREQ'], '14074000')

    def test_multiple_messages(self):
        data = "<CMD>PROGRAM <PROGRAM>Test</PROGRAM></CMD>\r\n<CMD>ENTER</CMD>\r\n"
        msgs = parse_messages(data)
        self.assertEqual(len(msgs), 2)

    def test_partial_buffer_ignored(self):
        data = "<CMD>ENTER</CMD>\r\n<CMD>PARTIAL"
        msgs = parse_messages(data)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['_type'], 'ENTER')

    def test_enterevent_fields(self):
        data = "<CMD>ENTEREVENT <CALL>N3FJP</CALL><FREQ>7074000</FREQ><MODE>FT8</MODE><EXCHANGE>3A ENY</EXCHANGE></CMD>\r\n"
        msgs = parse_messages(data)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['_type'], 'ENTEREVENT')
        self.assertEqual(msgs[0]['CALL'], 'N3FJP')
        self.assertEqual(msgs[0]['FREQ'], '7074000')
        self.assertEqual(msgs[0]['MODE'], 'FT8')

    def test_readbmfresponse(self):
        data = "<CMD>READBMFRESPONSE <BAND>20m</BAND><MODE>SSB</MODE><FREQ>14250000</FREQ></CMD>\r\n"
        msgs = parse_messages(data)
        self.assertEqual(msgs[0]['_type'], 'READBMFRESPONSE')
        self.assertEqual(msgs[0]['BAND'], '20m')


class TestBuildCmd(unittest.TestCase):
    def test_simple_command(self):
        result = build_cmd("ENTER")
        self.assertEqual(result, "<CMD>ENTER</CMD>\r\n")

    def test_command_with_fields(self):
        result = build_cmd("UPDATE", CALL="W1AW", FREQ="14074000")
        self.assertIn("<CMD>UPDATE", result)
        self.assertIn("<CALL>W1AW</CALL>", result)
        self.assertIn("<FREQ>14074000</FREQ>", result)
        self.assertTrue(result.endswith("</CMD>\r\n"))

    def test_terminator(self):
        result = build_cmd("PROGRAM", PROGRAM="FDLog")
        self.assertTrue(result.endswith("\r\n"))


class TestParseAdif(unittest.TestCase):
    def test_basic_adif(self):
        adif = "<CALL:4>W1AW<BAND:3>20m<MODE:3>SSB<FREQ:8>14.25000<TIME_ON:4>1234<EOR>"
        result = parse_adif(adif)
        self.assertEqual(result['CALL'], 'W1AW')
        self.assertEqual(result['BAND'], '20m')
        self.assertEqual(result['MODE'], 'SSB')
        self.assertEqual(result['FREQ'], '14.25000')
        self.assertEqual(result['TIME_ON'], '1234')

    def test_empty_string(self):
        result = parse_adif("")
        self.assertEqual(result, {})


class TestModeSuffix(unittest.TestCase):
    def test_cw(self):
        self.assertEqual(_mode_suffix("CW"), "c")

    def test_ssb(self):
        self.assertEqual(_mode_suffix("SSB"), "p")

    def test_ft8(self):
        self.assertEqual(_mode_suffix("FT8"), "d")

    def test_unknown_defaults_phone(self):
        self.assertEqual(_mode_suffix("UNKNOWN_MODE"), "p")


if __name__ == '__main__':
    unittest.main()
