"""Tests for utility functions in FDLog_Enhanced.py.

These functions cannot be imported directly because FDLog_Enhanced.py
has module-level side effects (argparse, tkinter, etc.).
We replicate the exact function bodies here for testing.
"""

import re
import time
import pytest


# Exact copies of the functions from FDLog_Enhanced.py for testing
def ival(s):
    """return value of leading int"""
    r = 0
    if s != "":
        mm = re.match(r' *(-?\d*)', s)
        if mm and mm.group(1):
            r = int(mm.group(1))
    return r


def tmtofl(a):
    """time to float in seconds, allow milliseconds"""
    return time.mktime((2000 + int(a[0:2]), int(a[2:4]), int(a[4:6]),
                        int(a[7:9]), int(a[9:11]), int(a[11:13]), 0, 0, 0))


def tmsub(a, b):
    """time subtract in seconds"""
    return tmtofl(a) - tmtofl(b)


class TestIval:
    """Tests for ival() - leading integer extraction."""

    def test_empty_string(self):
        assert ival("") == 0

    def test_plain_integer(self):
        assert ival("42") == 42

    def test_negative_integer(self):
        assert ival("-7") == -7

    def test_leading_spaces(self):
        assert ival("  10") == 10

    def test_mixed_string(self):
        assert ival("123abc") == 123

    def test_no_leading_digits(self):
        assert ival("abc") == 0

    def test_zero(self):
        assert ival("0") == 0

    def test_negative_with_trailing(self):
        assert ival("-5n") == -5

    def test_leading_space_negative(self):
        assert ival(" -3") == -3

    def test_float_string(self):
        assert ival("12.5") == 12

    def test_power_with_n(self):
        """Real-world: power field like '5n' for natural power."""
        assert ival("5n") == 5

    def test_power_field(self):
        assert ival("100") == 100


class TestTmtofl:
    """Tests for tmtofl() - time string to float conversion.

    Format: 'YYMMDD.HHMMSS' (13 chars with dot at position 6)
    """

    def test_basic_conversion(self):
        result = tmtofl("260628.180000")
        assert isinstance(result, float)

    def test_two_times_differ(self):
        t1 = tmtofl("260628.180000")
        t2 = tmtofl("260628.190000")
        assert t2 - t1 == pytest.approx(3600, abs=1)

    def test_one_minute_apart(self):
        t1 = tmtofl("260628.180000")
        t2 = tmtofl("260628.180100")
        assert t2 - t1 == pytest.approx(60, abs=1)

    def test_day_boundary(self):
        t1 = tmtofl("260628.235959")
        t2 = tmtofl("260629.000000")
        assert t2 - t1 == pytest.approx(1, abs=1)


class TestTmsub:
    """Tests for tmsub() - time subtraction in seconds."""

    def test_same_time(self):
        assert tmsub("260628.180000", "260628.180000") == pytest.approx(0, abs=1)

    def test_one_hour(self):
        assert tmsub("260628.190000", "260628.180000") == pytest.approx(3600, abs=1)

    def test_negative_result(self):
        result = tmsub("260628.180000", "260628.190000")
        assert result == pytest.approx(-3600, abs=1)

    def test_across_days(self):
        result = tmsub("260629.000000", "260628.230000")
        assert result == pytest.approx(3600, abs=1)
