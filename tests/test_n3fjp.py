"""Tests for N3FJP API protocol handling (n3fjp_integration.py).

These import the real module — no mocks — so protocol changes break loudly.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from n3fjp_integration import (
    N3FJPConfig, parse_messages, build_cmd, build_cmd_wrapped,
    parse_adif, _mode_suffix, BAND_FREQ_MAP,
)
from wsjtx_integration import freq_to_band


class TestParseMessages:
    """N3FJP sends XML-style <CMD>...</CMD> blocks over TCP."""

    def test_wrapper_tag_format(self):
        """N3FJP API v2 wraps fields in a command tag."""
        data = ("<CMD><ENTEREVENT><CALL>W1AW</CALL><CLASS>3A</CLASS>"
                "<ARRL_SECT>CT</ARRL_SECT></ENTEREVENT></CMD>")
        msgs = parse_messages(data)
        assert len(msgs) == 1
        assert msgs[0]['_type'] == 'ENTEREVENT'
        assert msgs[0]['CALL'] == 'W1AW'
        assert msgs[0]['CLASS'] == '3A'
        assert msgs[0]['ARRL_SECT'] == 'CT'

    def test_bare_word_format(self):
        """Older format: bare command word followed by fields."""
        msgs = parse_messages("<CMD>PROGRAM<PROGRAM>FDLog</PROGRAM></CMD>")
        assert len(msgs) == 1
        assert msgs[0]['_type'] == 'PROGRAM'
        assert msgs[0]['PROGRAM'] == 'FDLog'

    def test_bare_word_no_fields(self):
        msgs = parse_messages("<CMD>READBMF</CMD>")
        assert msgs[0]['_type'] == 'READBMF'

    def test_multiple_commands_in_one_buffer(self):
        """TCP stream can deliver several commands at once."""
        data = ("<CMD><SETUPDATESTATE><VALUE>TRUE</VALUE></SETUPDATESTATE></CMD>\r\n"
                "<CMD>READBMF</CMD>\r\n")
        msgs = parse_messages(data)
        assert [m['_type'] for m in msgs] == ['SETUPDATESTATE', 'READBMF']

    def test_field_keys_uppercased(self):
        msgs = parse_messages("<CMD><UPDATE><call>w1aw</call></UPDATE></CMD>")
        assert msgs[0]['CALL'] == 'w1aw'

    def test_no_cmd_blocks(self):
        assert parse_messages("garbage with no commands") == []

    def test_readbmf_response_fields(self):
        """READBMFRESPONSE carries band/mode/frequency; FREQ often 0."""
        data = ("<CMD><READBMFRESPONSE><BAND>20</BAND><MODE>PH</MODE>"
                "<FREQ>0</FREQ></READBMFRESPONSE></CMD>")
        msgs = parse_messages(data)
        assert msgs[0]['BAND'] == '20'
        assert msgs[0]['MODE'] == 'PH'
        assert msgs[0]['FREQ'] == '0'


class TestBuildCmd:
    def test_build_cmd_terminator(self):
        """N3FJP protocol requires \\r\\n message terminator."""
        assert build_cmd("READBMF").endswith("\r\n")
        assert build_cmd_wrapped("SETUPDATESTATE", VALUE="TRUE").endswith("\r\n")

    def test_build_cmd_wrapped_round_trip(self):
        """What we build must parse back identically."""
        raw = build_cmd_wrapped("ENTEREVENT", CALL="KD4SIR", CLASS="2A", ARRL_SECT="IN")
        msgs = parse_messages(raw)
        assert msgs[0]['_type'] == 'ENTEREVENT'
        assert msgs[0]['CALL'] == 'KD4SIR'
        assert msgs[0]['CLASS'] == '2A'
        assert msgs[0]['ARRL_SECT'] == 'IN'

    def test_build_cmd_round_trip(self):
        raw = build_cmd("PROGRAM", PROGRAM="FDLog")
        msgs = parse_messages(raw)
        assert msgs[0]['_type'] == 'PROGRAM'
        assert msgs[0]['PROGRAM'] == 'FDLog'


class TestParseAdif:
    def test_basic_record(self):
        rec = parse_adif("<CALL:4>W1AW<BAND:3>20M<MODE:3>SSB<EOR>")
        assert rec['CALL'] == 'W1AW'
        assert rec['BAND'] == '20M'
        assert rec['MODE'] == 'SSB'

    def test_type_suffixed_field(self):
        """ADIF allows <FIELD:len:type> — type must not break parsing."""
        rec = parse_adif("<CALL:4:S>W1AW")
        assert rec['CALL'] == 'W1AW'

    def test_n1mm_exchange_fields(self):
        rec = parse_adif("<APP_N1MM_EXCHANGE1:2>3A<APP_N1MM_EXCHANGE2:2>CT")
        assert rec['APP_N1MM_EXCHANGE1'] == '3A'
        assert rec['APP_N1MM_EXCHANGE2'] == 'CT'

    def test_value_whitespace_stripped(self):
        rec = parse_adif("<CALL:5>W1AW ")
        assert rec['CALL'] == 'W1AW'


class TestModeSuffix:
    """N3FJP mode strings map to FDLog band suffixes (c/p/d)."""

    def test_n3fjp_phone_modes(self):
        # N3FJP uses PH for phone, not SSB
        for m in ("PH", "SSB", "USB", "LSB", "AM", "FM"):
            assert _mode_suffix(m) == 'p'

    def test_n3fjp_digital_modes(self):
        # N3FJP uses DIG/DG for digital, not DIGI
        for m in ("DIG", "DG", "DIGI", "RTTY", "FT8", "FT4", "PSK31"):
            assert _mode_suffix(m) == 'd'

    def test_cw(self):
        assert _mode_suffix("CW") == 'c'

    def test_case_insensitive(self):
        assert _mode_suffix("ph") == 'p'
        assert _mode_suffix("dig") == 'd'

    def test_unknown_defaults_to_phone(self):
        assert _mode_suffix("SSTV") == 'p'


class TestConfigDefaults:
    def test_defaults(self):
        cfg = N3FJPConfig()
        assert cfg.client_port == 1100
        assert cfg.server_port == 1100
        assert cfg.host == "127.0.0.1"
        assert cfg.client_enabled is False
        assert cfg.server_enabled is False
        assert cfg.auto_log is True
        assert cfg.auto_band is True


class TestBandFreqMap:
    def test_band_freq_map_round_trip(self):
        """Every default frequency must land back in the same band."""
        for band, freq in BAND_FREQ_MAP.items():
            mapped = freq_to_band(freq)
            assert mapped is not None, "%s -> %d maps to no band" % (band, freq)
            # freq_to_band returns the digital suffix; compare band numbers
            assert mapped[:-1] == band[:-1], \
                "%s default freq %d maps to %s" % (band, freq, mapped)
