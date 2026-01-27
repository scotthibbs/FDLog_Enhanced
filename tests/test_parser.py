"""Tests for parser.py - CallSignParser."""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from parser import (
    CallSignParser, InvalidCallSignError, CallSignParserError
)


class TestValidateCallsign:
    """Tests for _validate_callsign()."""

    def test_valid_callsign(self):
        assert CallSignParser._validate_callsign("W1AW") == "W1AW"

    def test_strips_whitespace(self):
        assert CallSignParser._validate_callsign("  W1AW  ") == "W1AW"

    def test_none_raises(self):
        with pytest.raises(InvalidCallSignError, match="None"):
            CallSignParser._validate_callsign(None)

    def test_empty_raises(self):
        with pytest.raises(InvalidCallSignError, match="empty"):
            CallSignParser._validate_callsign("")

    def test_too_short_raises(self):
        with pytest.raises(InvalidCallSignError, match="at least 3"):
            CallSignParser._validate_callsign("W1")

    def test_no_digit_raises(self):
        with pytest.raises(InvalidCallSignError, match="digit"):
            CallSignParser._validate_callsign("WAAW")

    def test_no_letter_raises(self):
        with pytest.raises(InvalidCallSignError, match="letter"):
            CallSignParser._validate_callsign("123")

    def test_list_input(self):
        assert CallSignParser._validate_callsign(['W', '1', 'A', 'W']) == "W1AW"


class TestParseCallsign:
    """Tests for parse_callsign() - prefix/separator/suffix splitting."""

    def test_standard_us_call(self):
        prefix, sep, suffix = CallSignParser.parse_callsign("W1AW")
        assert prefix == "W"
        assert sep == "1"
        assert suffix == "AW"

    def test_two_letter_prefix(self):
        prefix, sep, suffix = CallSignParser.parse_callsign("WB4GHJ")
        assert prefix == "WB"
        assert sep == "4"
        assert suffix == "GHJ"

    def test_single_letter_suffix(self):
        prefix, sep, suffix = CallSignParser.parse_callsign("N5A")
        assert prefix == "N"
        assert sep == "5"
        assert suffix == "A"

    def test_number_prefix_start(self):
        # Calls like 4X1ABC (Israel)
        prefix, sep, suffix = CallSignParser.parse_callsign("4X1ABC")
        assert sep == "1"
        assert suffix == "ABC"

    def test_two_digit_prefix(self):
        prefix, sep, suffix = CallSignParser.parse_callsign("3D2ABC")
        assert sep == "2"
        assert suffix == "ABC"

    def test_slash_portable(self):
        # W1AW/4 should still parse the base call
        prefix, sep, suffix = CallSignParser.parse_callsign("W1AW/4")
        assert prefix == "W"
        assert sep == "1"
        assert suffix == "AW"

    def test_kd4sir(self):
        prefix, sep, suffix = CallSignParser.parse_callsign("KD4SIR")
        assert prefix == "KD"
        assert sep == "4"
        assert suffix == "SIR"


class TestLookupCountry:
    """Tests for lookup_country() - requires cty.dat file."""

    @pytest.fixture(autouse=True)
    def check_cty_file(self):
        """Skip tests if cty.dat is not available."""
        cty_path = CallSignParser.get_cty_file_path()
        if not os.path.exists(cty_path):
            pytest.skip("cty.dat not found")

    def test_us_prefix(self):
        result = CallSignParser.lookup_country("W", "1")
        assert "United States" in result

    def test_uk_prefix(self):
        result = CallSignParser.lookup_country("G", "3")
        assert "England" in result

    def test_unassigned(self):
        result = CallSignParser.lookup_country("ZZZ", "0")
        assert result == "unassigned?"


class TestIsValidPrefix:

    def test_valid(self):
        assert CallSignParser.is_valid_prefix("United States") is True

    def test_unassigned(self):
        assert CallSignParser.is_valid_prefix("unassigned?") is False

    def test_empty(self):
        assert CallSignParser.is_valid_prefix("") is False


class TestParse:
    """Tests for parse() - end-to-end."""

    @pytest.fixture(autouse=True)
    def check_cty_file(self):
        cty_path = CallSignParser.get_cty_file_path()
        if not os.path.exists(cty_path):
            pytest.skip("cty.dat not found")

    def test_full_parse_us(self):
        prefix, sep, suffix, country, is_valid = CallSignParser.parse("W1AW")
        assert prefix == "W"
        assert sep == "1"
        assert suffix == "AW"
        assert "United States" in country
        assert is_valid is True

    def test_invalid_raises(self):
        with pytest.raises(InvalidCallSignError):
            CallSignParser.parse("")
