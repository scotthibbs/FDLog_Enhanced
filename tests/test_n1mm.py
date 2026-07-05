"""Tests for N1MM+ UDP broadcast integration (n1mm_integration.py).

These import the real module - no mocks - so protocol changes break loudly.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from n1mm_integration import (
    N1MMConfig, N1MMListener, parse_message, build_report,
    n1mm_freq_to_band_mode, _extract_freq_hz, _mode_suffix,
)


def _contactinfo_xml(**overrides):
    fields = {
        'call': 'K1ABC', 'mycall': 'W1AW', 'band': '7', 'txfreq': '703500',
        'rxfreq': '703500', 'mode': 'CW', 'exchange1': '1D', 'section': 'CT',
        'timestamp': '2026-06-27 18:32:12', 'isoriginal': 'True',
    }
    fields.update(overrides)
    body = ''.join(f'<{k}>{v}</{k}>' for k, v in fields.items())
    return f'<contactinfo>{body}</contactinfo>'.encode('utf-8')


class TestParseMessage:
    def test_contactinfo_fields_lowercased(self):
        msg = parse_message(_contactinfo_xml())
        assert msg['_type'] == 'contactinfo'
        assert msg['call'] == 'K1ABC'
        assert msg['exchange1'] == '1D'
        assert msg['section'] == 'CT'

    def test_contactreplace_type(self):
        msg = parse_message(b'<contactreplace><call>W1AW</call><oldcall>W1AX</oldcall></contactreplace>')
        assert msg['_type'] == 'contactreplace'
        assert msg['oldcall'] == 'W1AX'

    def test_contactdelete_type(self):
        msg = parse_message(b'<contactdelete><call>W1AW</call></contactdelete>')
        assert msg['_type'] == 'contactdelete'

    def test_radioinfo_type(self):
        msg = parse_message(b'<RadioInfo><Freq>352211</Freq><Mode>CW</Mode></RadioInfo>')
        assert msg['_type'] == 'radioinfo'
        assert msg['freq'] == '352211'

    def test_non_xml_returns_none(self):
        assert parse_message(b'not xml at all') is None

    def test_malformed_xml_returns_none(self):
        assert parse_message(b'<contactinfo><call>W1AW</contactinfo>') is None

    def test_empty_element_becomes_empty_string(self):
        msg = parse_message(b'<contactinfo><name></name></contactinfo>')
        assert msg['name'] == ''


class TestModeSuffix:
    def test_cw(self):
        assert _mode_suffix('CW') == 'c'

    def test_phone_modes(self):
        for m in ('USB', 'LSB', 'AM', 'FM', 'SSB'):
            assert _mode_suffix(m) == 'p'

    def test_digital_modes(self):
        for m in ('RTTY', 'PSK31', 'FT8', 'FT4'):
            assert _mode_suffix(m) == 'd'

    def test_case_insensitive(self):
        assert _mode_suffix('cw') == 'c'

    def test_unknown_defaults_to_phone(self):
        assert _mode_suffix('SSTV') == 'p'


class TestExtractFreqHz:
    def test_txfreq_tens_of_hz(self):
        # N1MM+ frequencies are tens of Hz: 703500 -> 7,035,000 Hz
        assert _extract_freq_hz({'txfreq': '703500'}) == 7035000

    def test_prefers_txfreq_over_rxfreq(self):
        assert _extract_freq_hz({'txfreq': '703500', 'rxfreq': '703600'}) == 7035000

    def test_falls_back_to_rxfreq(self):
        assert _extract_freq_hz({'rxfreq': '703500'}) == 7035000

    def test_falls_back_to_band_mhz(self):
        assert _extract_freq_hz({'band': '7'}) == 7000000

    def test_band_field_locale_comma_decimal(self):
        # Some locales format the 'band' tag with a comma decimal separator
        assert _extract_freq_hz({'band': '3,573'}) == 3573000

    def test_all_missing_returns_zero(self):
        assert _extract_freq_hz({}) == 0

    def test_radioinfo_keys(self):
        assert _extract_freq_hz({'freq': '352211'}, keys=('txfreq', 'freq')) == 3522110


class TestFreqToBandMode:
    def test_cw_forty_meters(self):
        assert n1mm_freq_to_band_mode(7035000, 'CW') == '40c'

    def test_phone_twenty_meters(self):
        assert n1mm_freq_to_band_mode(14250000, 'USB') == '20p'

    def test_digital_forty_meters(self):
        assert n1mm_freq_to_band_mode(7074000, 'FT8') == '40d'

    def test_zero_freq_returns_none(self):
        assert n1mm_freq_to_band_mode(0, 'CW') is None

    def test_out_of_band_returns_none(self):
        assert n1mm_freq_to_band_mode(1000, 'CW') is None


class TestBuildReport:
    def test_combines_class_and_section(self):
        assert build_report('1D', 'CT') == '1d ct'

    def test_missing_section(self):
        assert build_report('1D', '') == '1d'

    def test_missing_class(self):
        assert build_report('', 'CT') == 'ct'

    def test_both_empty(self):
        assert build_report('', '') == ''

    def test_strips_whitespace(self):
        assert build_report(' 1D ', ' CT ') == '1d ct'


class TestConfigDefaults:
    def test_defaults(self):
        cfg = N1MMConfig()
        assert cfg.udp_port == 12060
        assert cfg.udp_ip == "0.0.0.0"
        assert cfg.enabled is False
        assert cfg.auto_log is True
        assert cfg.auto_band is True
        assert cfg.only_original is True


class TestListenerHandling:
    """Drive N1MMListener._handle_message directly - no real socket needed."""

    def _make_listener(self, **config_overrides):
        logged, deleted, replaced, band_changes = [], [], [], []
        cfg = N1MMConfig(**config_overrides)
        listener = N1MMListener(
            cfg,
            on_qso_logged=lambda call, band_mode, report, ts: logged.append((call, band_mode, report, ts)),
            on_status_update=lambda status: None,
            on_band_change=lambda b: band_changes.append(b),
            on_qso_deleted=lambda call, msg: deleted.append(call),
            on_qso_replaced=lambda call, msg: replaced.append(call),
        )
        return listener, logged, deleted, replaced, band_changes

    def test_contactinfo_logs_qso(self):
        listener, logged, *_ = self._make_listener()
        listener._handle_message(parse_message(_contactinfo_xml()))
        assert logged == [('K1ABC', '40c', '1d ct', None)]

    def test_auto_log_disabled_suppresses_logging(self):
        listener, logged, *_ = self._make_listener(auto_log=False)
        listener._handle_message(parse_message(_contactinfo_xml()))
        assert logged == []

    def test_only_original_skips_relayed_contact(self):
        listener, logged, *_ = self._make_listener(only_original=True)
        listener._handle_message(parse_message(_contactinfo_xml(isoriginal='False')))
        assert logged == []

    def test_only_original_false_logs_relayed_contact(self):
        listener, logged, *_ = self._make_listener(only_original=False)
        listener._handle_message(parse_message(_contactinfo_xml(isoriginal='False')))
        assert len(logged) == 1

    def test_missing_isoriginal_defaults_to_original(self):
        xml = b'<contactinfo><call>K1ABC</call><txfreq>703500</txfreq><mode>CW</mode></contactinfo>'
        listener, logged, *_ = self._make_listener(only_original=True)
        listener._handle_message(parse_message(xml))
        assert len(logged) == 1

    def test_empty_call_ignored(self):
        xml = b'<contactinfo><call></call><txfreq>703500</txfreq><mode>CW</mode></contactinfo>'
        listener, logged, *_ = self._make_listener()
        listener._handle_message(parse_message(xml))
        assert logged == []

    def test_unresolvable_frequency_ignored(self):
        xml = b'<contactinfo><call>K1ABC</call><mode>CW</mode></contactinfo>'
        listener, logged, *_ = self._make_listener()
        listener._handle_message(parse_message(xml))
        assert logged == []

    def test_contactdelete_calls_callback(self):
        listener, logged, deleted, *_ = self._make_listener()
        listener._handle_message(parse_message(b'<contactdelete><call>K1ABC</call></contactdelete>'))
        assert deleted == ['K1ABC']
        assert logged == []

    def test_contactreplace_uses_replaced_callback_when_present(self):
        listener, logged, deleted, replaced, _ = self._make_listener()
        listener._handle_message(parse_message(b'<contactreplace><call>K1ABC</call></contactreplace>'))
        assert replaced == ['K1ABC']
        assert logged == []

    def test_contactreplace_falls_back_to_logging_without_callback(self):
        cfg = N1MMConfig()
        logged = []
        listener = N1MMListener(
            cfg,
            on_qso_logged=lambda call, band_mode, report, ts: logged.append(call),
            on_status_update=lambda status: None,
        )
        xml = _contactinfo_xml().replace(b'contactinfo', b'contactreplace')
        listener._handle_message(parse_message(xml))
        assert logged == ['K1ABC']

    def test_radioinfo_triggers_band_change(self):
        listener, logged, deleted, replaced, band_changes = self._make_listener()
        listener._handle_message(parse_message(b'<RadioInfo><TXFreq>703500</TXFreq><Mode>CW</Mode></RadioInfo>'))
        assert band_changes == ['40c']

    def test_radioinfo_auto_band_disabled_suppresses_callback(self):
        listener, logged, deleted, replaced, band_changes = self._make_listener(auto_band=False)
        listener._handle_message(parse_message(b'<RadioInfo><TXFreq>703500</TXFreq><Mode>CW</Mode></RadioInfo>'))
        assert band_changes == []
