"""Wire-format spec tests for the internet-relay TCP framing.

FDLog_Enhanced.py can't be imported without starting the app, so — like the
MockQsoDb tests — these verify the *specification* that _tcp_frame() and
_tcp_recv_one() implement (FDLog_Enhanced.py, NetworkSync). If the framing
code there changes, these tests define what remote nodes on older versions
still expect on the wire:

    header byte 0: length & 255
    header byte 1: length >> 8
    header byte 2: byte0 XOR byte1   (parity — used to re-sync a torn stream)
    sane length:   1..8200

A reader that sees a bad parity byte or an insane length slides its window
forward one byte and tries again.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def frame(amsg: bytes) -> bytes:
    """Reference implementation of NetworkSync._tcp_frame()."""
    n = len(amsg)
    i, j = n & 255, n >> 8
    return bytes([i, j, i ^ j]) + amsg


def read_frames(stream: bytes):
    """Reference reader implementing _tcp_recv_one()'s resync loop over a
    byte string instead of a socket. Returns list of recovered messages."""
    out = []
    pos = 0
    while pos + 3 <= len(stream):
        b0, b1, b2 = stream[pos], stream[pos + 1], stream[pos + 2]
        if b0 ^ b1 != b2:            # bad parity — slide window
            pos += 1
            continue
        length = b0 + 256 * b1
        if length == 0 or length > 8200:  # sanity check — slide window
            pos += 1
            continue
        if pos + 3 + length > len(stream):
            break                    # incomplete tail
        out.append(stream[pos + 3:pos + 3 + length])
        pos += 3 + length
    return out


class TestFrameFormat:
    def test_header_math_small(self):
        f = frame(b"hello")
        assert f[0] == 5 and f[1] == 0 and f[2] == 5
        assert f[3:] == b"hello"

    def test_header_math_multibyte_length(self):
        msg = b"x" * 1000               # 1000 = 0x03E8
        f = frame(msg)
        assert f[0] == 0xE8 and f[1] == 0x03 and f[2] == 0xE8 ^ 0x03
        assert f[0] + 256 * f[1] == 1000

    def test_parity_always_consistent(self):
        for n in (1, 255, 256, 4096, 8200):
            f = frame(b"y" * n)
            assert f[0] ^ f[1] == f[2]

    def test_round_trip_single(self):
        assert read_frames(frame(b"q|node1|5|...")) == [b"q|node1|5|..."]

    def test_round_trip_stream(self):
        """Multiple frames back to back, as a TCP stream delivers them."""
        msgs = [b"first", b"second message", b"z" * 300]
        stream = b"".join(frame(m) for m in msgs)
        assert read_frames(stream) == msgs


class TestResync:
    def test_leading_garbage_skipped(self):
        """Reader slides forward past junk until parity+length make sense."""
        stream = b"\xff\xfe" + frame(b"good")
        assert read_frames(stream) == [b"good"]

    def test_zero_length_rejected(self):
        # 0-length header has valid parity (0^0==0) but fails sanity check
        stream = bytes([0, 0, 0]) + frame(b"good")
        assert read_frames(stream) == [b"good"]

    def test_insane_length_rejected(self):
        # length 65535 has valid parity but exceeds the 8200 cap
        stream = bytes([255, 255, 0]) + frame(b"good")
        assert read_frames(stream) == [b"good"]

    def test_incomplete_tail_not_returned(self):
        stream = frame(b"complete") + frame(b"cut off")[:-3]
        assert read_frames(stream) == [b"complete"]
