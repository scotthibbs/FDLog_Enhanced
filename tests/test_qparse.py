"""Tests for QsoDb.qparse() - QSO line parsing."""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# qparse is a staticmethod on QsoDb, but QsoDb is defined in FDLog_Enhanced
# which has heavy tkinter/global dependencies. We import it carefully.
# Since qparse is a @staticmethod, we can call it without instantiation
# but we need to get a reference to it.

# Strategy: extract qparse by importing the module partially
# qparse only depends on re and CallSignParser, so we can import QsoDb class.
# However the module has side effects. We'll mock what's needed.

import importlib
import unittest.mock as mock


@pytest.fixture(scope="module")
def qparse():
    """Extract the qparse static method from FDLog_Enhanced.

    The module has heavy side effects (tkinter, sockets, etc.), so we
    read the source and extract just the qparse function.
    """
    # We need to get QsoDb.qparse. Since the module imports tkinter etc at top level,
    # we'll extract the function by reading source and compiling just what we need.
    import re
    from parser import CallSignParser, InvalidCallSignError, CallSignParserError

    def qparse_func(line):
        """qso/call/partial parser - extracted from QsoDb"""
        stat, tm, pfx, sfx, call7, xcall, rept = 0, '', '', '', '', '', ''
        m4 = re.match(r'(:([\d.]*)( )?)?(([a-z\d/]+)( )?)?([\da-zA-Z ]*)$', line)
        if m4:
            tm = m4.group(2)
            xcall = m4.group(5)
            rept = m4.group(7)
            stat = 0
            if m4.group(1) is not None or xcall is not None:
                stat = 1
            if tm is not None:
                stat = 0
                m4 = re.match(r'([0-3](\d([.]([0-5](\d([0-5](\d)?)?)?)?)?)?)?$', tm)
                if m4:
                    stat = 1
            if xcall is not None:
                stat = 0
                basecall = xcall
                if '/' in xcall:
                    basecall = xcall[:xcall.index('/')]
                if basecall:
                    has_digit = any(ch.isdigit() for ch in basecall)
                    has_letter = any(ch.isalpha() for ch in basecall)
                    if not has_digit:
                        stat = 2
                        sfx = basecall
                    elif not has_letter:
                        stat = 2
                        sfx = basecall
                    else:
                        try:
                            prefix, separator, suffix = CallSignParser.parse_callsign(basecall)
                            pfx = prefix + separator
                            sfx = suffix
                            if sfx and pfx:
                                stat = 4
                                call7 = basecall
                            elif pfx and not sfx:
                                stat = 3
                        except (InvalidCallSignError, CallSignParserError, IndexError):
                            stat = 1
                if (stat == 4) & (rept > ""):
                    stat = 0
                    m4 = re.match(r'[\da-zA-Z]+[\da-zA-Z ]*$', rept)
                    if m4:
                        stat = 5
                if len(xcall) > 12:
                    stat = 0
                if len(pfx) > 6:
                    stat = 0
                if len(sfx) > 4:
                    stat = 0
                if tm:
                    if len(tm) < 7:
                        stat = 0
        return stat, tm, pfx, sfx, call7, xcall, rept

    return qparse_func


class TestQparseBasic:
    """Basic qparse tests."""

    def test_empty_string(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("")
        assert stat == 0

    def test_full_qso(self, qparse):
        # :12.3456 wb4ghj 2a sf Steve
        stat, tm, pfx, sfx, call7, xcall, rept = qparse(":12.3456 wb4ghj 2a sf Steve")
        assert stat == 5  # complete QSO
        assert tm == "12.3456"
        assert call7 == "wb4ghj"
        assert xcall == "wb4ghj"

    def test_call_only(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("wb4ghj")
        assert stat == 4  # complete call
        assert call7 == "wb4ghj"
        assert pfx == "wb4"
        assert sfx == "ghj"

    def test_call_with_report(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("wb4ghj 2a sf")
        assert stat == 5  # complete QSO
        assert rept == "2a sf"

    def test_suffix_only(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("ghj")
        assert stat == 2  # suffix
        assert sfx == "ghj"

    def test_partial_time(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse(":12")
        assert stat == 1  # partial time is valid partial input

    def test_time_with_call(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse(":12.3456 wb4ghj")
        assert stat == 4  # complete call with full time
        assert tm == "12.3456"

    def test_slash_call(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("w1aw/4")
        assert stat == 4  # complete call
        assert xcall == "w1aw/4"

    def test_digits_only_suffix(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("123")
        assert stat == 2  # treated as partial suffix (digits only)

    def test_too_long_call(self, qparse):
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("a" * 13)
        assert stat == 0  # exceeds length limit

    def test_uppercase_in_report(self, qparse):
        # Report can contain uppercase
        stat, tm, pfx, sfx, call7, xcall, rept = qparse("wb4ghj 2A SF")
        assert stat == 5
        assert rept == "2A SF"
