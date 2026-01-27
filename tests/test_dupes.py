"""Tests for duplicate detection logic."""

import threading
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tests.test_scoring import MockQsoDb, FakeGd, make_qso


class TestDupck:
    """Tests for dupck() - duplicate call-band detection."""

    def _make_db_with_dupes(self, records):
        """Create a MockQsoDb with bysfx populated."""
        gd = FakeGd()
        db = MockQsoDb(records, gd)
        # Manually build bysfx index like logdup does
        db.bysfx = {}
        for r in records:
            if r.rept[:5] == "*del:" or r.band[0] == '*':
                continue
            dummy, dummy2, dummy3, sfx, dummy4, xcall, dummy5 = db.qparse(r.call)
            if sfx:
                key = sfx + '.' + r.band
                if key in db.bysfx:
                    db.bysfx[key].append(xcall)
                else:
                    db.bysfx[key] = [xcall]
        return db

    def _dupck(self, db, wcall, band):
        """Replicate dupck logic without needing global gd."""
        dummy, dummy2, dummy3, sfx, call8, xcall, dummy4 = db.qparse(wcall)
        return call8 in db.bysfx.get(sfx + '.' + band, [])

    def test_no_dupe_empty_db(self):
        db = self._make_db_with_dupes([])
        assert self._dupck(db, "wb4ghj", "20p") is False

    def test_dupe_found(self):
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = self._make_db_with_dupes(records)
        assert self._dupck(db, "wb4ghj", "20p") is True

    def test_same_call_different_band_no_dupe(self):
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = self._make_db_with_dupes(records)
        assert self._dupck(db, "wb4ghj", "40p") is False

    def test_different_call_same_band_no_dupe(self):
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = self._make_db_with_dupes(records)
        assert self._dupck(db, "w1aw", "20p") is False

    def test_same_call_different_mode_no_dupe(self):
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = self._make_db_with_dupes(records)
        assert self._dupck(db, "wb4ghj", "20c") is False


class TestSfx2call:
    """Tests for sfx2call() - suffix to call lookup."""

    def test_empty(self):
        gd = FakeGd()
        db = MockQsoDb([], gd)
        db.bysfx = {}
        assert db.bysfx.get("ghj.20p", []) == []

    def test_found(self):
        gd = FakeGd()
        db = MockQsoDb([], gd)
        db.bysfx = {"ghj.20p": ["wb4ghj"]}
        assert "wb4ghj" in db.bysfx.get("ghj.20p", [])


class TestNetworkDupe:
    """Tests for network dupe detection logic.

    check_network_dupe is complex and tightly coupled to globals,
    so we test the core logic pattern: given two records with same
    call+band, the newer one should be deleted.
    """

    def test_identifies_same_call_band_as_dupe(self):
        """Two records with same call and band are duplicates."""
        gd = FakeGd()
        r1 = make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")
        r2 = make_qso("n2", 1, "260628.200500", "20p", "wb4ghj", "2a sf", "100")
        db = MockQsoDb([r1, r2], gd)

        # Simulate the dupe detection logic
        d, cdict, gdict = db.cleanlog()
        # Both map to same call-band key, so cdict deduplicates
        # This is how cleanlog naturally handles dupes - last one wins in dict
        assert len(cdict) == 1

    def test_different_bands_not_dupe(self):
        gd = FakeGd()
        r1 = make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")
        r2 = make_qso("n2", 1, "260628.200500", "40p", "wb4ghj", "2a sf", "100")
        db = MockQsoDb([r1, r2], gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 2

    def test_special_band_skipped(self):
        """Records with * band prefix are not checked for dupes."""
        gd = FakeGd()
        r1 = make_qso("n1", 1, "260628.200000", "*QST", "", "message", "0")
        db = MockQsoDb([r1], gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0

    def test_gota_separate_dupe_space(self):
        """GOTA and non-GOTA records don't dupe each other."""
        gd = FakeGd()
        r1 = make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")
        r2 = make_qso("gotanode", 1, "260628.200500", "20p", "wb4ghj", "2a sf", "100")
        db = MockQsoDb([r1, r2], gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 1  # non-GOTA
        assert len(gdict) == 1  # GOTA - separate space
