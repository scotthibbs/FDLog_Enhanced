"""Tests for scoring logic - cleanlog() and band_rpt()."""

import threading
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def make_qso(src, seq, date, band, call, rept, powr, oper="op", logr="lg"):
    """Create a mock QSO record."""
    q = type('Q', (), {})()
    q.src = src
    q.seq = seq
    q.date = date
    q.band = band
    q.call = call
    q.rept = rept
    q.powr = powr
    q.oper = oper
    q.logr = logr
    return q


class FakeGd:
    """Fake global database for testing."""
    def __init__(self, fdstrt="260628.180000", fdend="260629.180000"):
        self._vals = {'fdstrt': fdstrt, 'fdend': fdend}

    def getv(self, key):
        return self._vals.get(key, '')


class MockQsoDb:
    """Minimal QsoDb mock with cleanlog and band_rpt logic extracted."""

    def __init__(self, records, gd):
        self.byid = {}
        self.lock = threading.RLock()
        self.gd = gd
        for r in records:
            key = "%s.%s" % (r.src, r.seq)
            self.byid[key] = r

    @staticmethod
    def qparse(line):
        """Minimal qparse for testing - just return call as-is."""
        import re
        from parser import CallSignParser, InvalidCallSignError, CallSignParserError
        stat, tm, pfx, sfx, call7, xcall, rept = 0, '', '', '', '', '', ''
        m4 = re.match(r'(:([\d.]*)( )?)?(([a-z\d/]+)( )?)?([\da-zA-Z ]*)$', line)
        if m4:
            xcall = m4.group(5)
            if xcall:
                basecall = xcall
                if '/' in xcall:
                    basecall = xcall[:xcall.index('/')]
                if basecall:
                    has_digit = any(ch.isdigit() for ch in basecall)
                    has_letter = any(ch.isalpha() for ch in basecall)
                    if has_digit and has_letter:
                        try:
                            prefix, separator, suffix = CallSignParser.parse_callsign(basecall)
                            pfx = prefix + separator
                            sfx = suffix
                            if sfx and pfx:
                                call7 = basecall
                        except:
                            pass
        return stat, tm, pfx, sfx, call7, xcall, rept

    def _ival(self, s):
        r = 0
        if s != "":
            import re
            mm = re.match(r' *(-?\d*)', s)
            if mm and mm.group(1):
                r = int(mm.group(1))
        return r

    def cleanlog(self):
        """Simplified cleanlog matching real logic."""
        d, cdict, gdict = {}, {}, {}
        fdstart = self.gd.getv('fdstrt')
        fdend = self.gd.getv('fdend')
        with self.lock:
            for index in list(self.byid.values()):
                strsrcseq = "%s|%s" % (index.src, index.seq)
                d[strsrcseq] = index
        # process deletes
        for index in list(d.keys()):
            if index in d:
                iv = d[index]
                if iv.rept[:5] == "*del:":
                    dummy, st, sn, dummy = iv.rept.split(':')
                    strsrcseq = "%s|%s" % (st, sn)
                    if strsrcseq in list(d.keys()):
                        del d[strsrcseq]
                    del d[index]
        # filter time window
        for index in list(d.keys()):
            iv = d[index]
            if iv.date < fdstart or iv.date > fdend:
                del d[index]
        # re-index by call-band
        for index in list(d.values()):
            dummy, dummy, dummy, dummy, call1, dummy, dummy = self.qparse(index.call)
            strsrcseq = "%s-%s" % (call1, index.band)
            if self._ival(index.powr) == 0 and index.band[0] != '*':
                continue
            if index.band == 'off':
                continue
            if index.band[0] == '*':
                continue
            if index.src == 'gotanode':
                gdict[strsrcseq] = index
            else:
                cdict[strsrcseq] = index
        return d, cdict, gdict

    def band_rpt(self):
        """Simplified band_rpt matching real logic."""
        qpb, ppb, qpop, qplg, qpst, tq, score, maxp = {}, {}, {}, {}, {}, 0, 0, 0
        cwq, digq, fonq = 0, 0, 0
        qpgop, gotaq, nat, sat = {}, 0, [], []
        import re
        dummy, c1, g3 = self.cleanlog()
        for i10 in list(c1.values()) + list(g3.values()):
            if re.search('sat', i10.band):
                sat.append(i10)
            if 'n' in i10.powr:
                nat.append(i10)
            if i10.src == 'gotanode':
                qpgop[i10.oper] = qpgop.get(i10.oper, 0) + 1
                qpop[i10.oper] = qpop.get(i10.oper, 0) + 1
                qplg[i10.logr] = qplg.get(i10.logr, 0) + 1
                qpst[i10.src] = qpst.get(i10.src, 0) + 1
                if gotaq >= 500:
                    continue
                gotaq += 1
                tq += 1
                score += 1
                if 'c' in i10.band:
                    cwq += 1
                    score += 1
                    qpb['gotac'] = qpb.get('gotac', 0) + 1
                    ppb['gotac'] = max(ppb.get('gotac', 0), self._ival(i10.powr))
                if 'd' in i10.band:
                    digq += 1
                    score += 1
                    qpb['gotad'] = qpb.get('gotad', 0) + 1
                    ppb['gotad'] = max(ppb.get('gotad', 0), self._ival(i10.powr))
                if 'p' in i10.band:
                    fonq += 1
                    qpb['gotap'] = qpb.get('gotap', 0) + 1
                    ppb['gotap'] = max(ppb.get('gotap', 0), self._ival(i10.powr))
                continue
            qpb[i10.band] = qpb.get(i10.band, 0) + 1
            ppb[i10.band] = max(ppb.get(i10.band, 0), self._ival(i10.powr))
            maxp = max(maxp, self._ival(i10.powr))
            qpop[i10.oper] = qpop.get(i10.oper, 0) + 1
            qplg[i10.logr] = qplg.get(i10.logr, 0) + 1
            qpst[i10.src] = qpst.get(i10.src, 0) + 1
            score += 1
            tq += 1
            if 'c' in i10.band:
                score += 1
                cwq += 1
            if 'd' in i10.band:
                score += 1
                digq += 1
            if 'p' in i10.band:
                fonq += 1
        return qpb, ppb, qpop, qplg, qpst, tq, score, maxp, cwq, digq, fonq, qpgop, gotaq, nat, sat


class TestCleanlog:
    """Tests for cleanlog filtering."""

    def test_basic_record_included(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 1

    def test_deleted_record_excluded(self):
        gd = FakeGd()
        records = [
            make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100"),
            make_qso("n1", 2, "260628.200100", "20p", "wb4ghj", "*del:n1:1:dupe", "0"),
        ]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0

    def test_out_of_window_excluded(self):
        gd = FakeGd()
        # Record before contest start
        records = [make_qso("n1", 1, "260627.120000", "20p", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0

    def test_zero_power_excluded(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "0")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0

    def test_special_band_excluded(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "*QST", "wb4ghj", "msg", "100")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0

    def test_gota_goes_to_gdict(self):
        gd = FakeGd()
        records = [make_qso("gotanode", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0
        assert len(gdict) == 1

    def test_off_band_excluded(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "off", "wb4ghj", "test", "100")]
        db = MockQsoDb(records, gd)
        d, cdict, gdict = db.cleanlog()
        assert len(cdict) == 0


class TestBandRpt:
    """Tests for band_rpt scoring."""

    def test_phone_scores_one_point(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        qpb, ppb, qpop, qplg, qpst, tq, score, maxp, cwq, digq, fonq, *_ = result
        assert tq == 1
        assert score == 1  # phone = 1 point
        assert fonq == 1
        assert cwq == 0

    def test_cw_scores_two_points(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20c", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        tq, score, cwq = result[5], result[6], result[8]
        assert tq == 1
        assert score == 2  # CW = 2 points
        assert cwq == 1

    def test_digital_scores_two_points(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20d", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        tq, score, digq = result[5], result[6], result[9]
        assert tq == 1
        assert score == 2
        assert digq == 1

    def test_max_power_tracked(self):
        gd = FakeGd()
        records = [
            make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100"),
            make_qso("n1", 2, "260628.200100", "40p", "w1aw", "3a ct", "150"),
        ]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        maxp = result[7]
        assert maxp == 150

    def test_gota_cap_at_500(self):
        gd = FakeGd()
        # Create 510 GOTA records with unique call-band combos
        # Use unique calls and bands so cleanlog doesn't dedup them
        bands = ["20p", "20c", "20d", "40p", "40c", "40d", "80p", "80c", "80d", "15p"]
        records = []
        for i in range(510):
            # Generate unique call per record
            prefix_letter = chr(ord('a') + (i % 26))
            suffix = "%s%s" % (chr(ord('a') + (i // 260) % 26), chr(ord('a') + (i // 10) % 26))
            call = "w%d%s" % ((i % 10), suffix)
            band = bands[i % len(bands)]
            records.append(make_qso(
                "gotanode", i + 1, "260628.200000", band,
                call, "2a sf", "100", oper="go"
            ))
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        tq, gotaq = result[5], result[12]
        assert gotaq == 500
        assert tq == 500  # capped at 500

    def test_natural_power_tracked(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "5n")]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        nat = result[13]
        assert len(nat) == 1

    def test_satellite_tracked(self):
        gd = FakeGd()
        records = [make_qso("n1", 1, "260628.200000", "satd", "wb4ghj", "2a sf", "100")]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        sat = result[14]
        assert len(sat) == 1

    def test_multiple_bands(self):
        gd = FakeGd()
        records = [
            make_qso("n1", 1, "260628.200000", "20p", "wb4ghj", "2a sf", "100"),
            make_qso("n1", 2, "260628.200100", "20c", "w1aw", "3a ct", "100"),
            make_qso("n1", 3, "260628.200200", "40d", "n5a", "1a ok", "100"),
        ]
        db = MockQsoDb(records, gd)
        result = db.band_rpt()
        qpb, tq, score = result[0], result[5], result[6]
        assert tq == 3
        assert score == 5  # 1 phone + 2 cw + 2 dig
        assert qpb.get("20p", 0) == 1
        assert qpb.get("20c", 0) == 1
        assert qpb.get("40d", 0) == 1
