"""Tests for _warn_udp_port_conflict() in FDLog_Enhanced.py.

FDLog_Enhanced.py can't be imported directly (module-level tkinter/argparse
side effects) - like test_utils.py and test_tcp_framing.py, we replicate the
exact function body here. Only modal=False is exercised: modal=True pops a
real Tk dialog via tkinter.messagebox, which needs a live display and was
verified manually (see project memory) rather than in this headless suite.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# Exact copy of the function from FDLog_Enhanced.py for testing
def _warn_udp_port_conflict(this_name, this_port, other_name, other_listener, modal=True):
    if not (other_listener and other_listener._running):
        return
    if other_listener.config.udp_port != this_port:
        return
    print(f"WARNING: {this_name} and {other_name} are both configured for UDP port {this_port}")
    if modal:
        try:
            import tkinter.messagebox
            tkinter.messagebox.showwarning(
                "UDP Port Conflict",
                f"{this_name} and {other_name} are both set to listen on UDP port {this_port}.\n\n"
                f"Only one of them will reliably receive broadcasts on that port - "
                f"QSOs may be missed, or show up under the wrong status label.\n\n"
                f"Change one of them to a different port in its Settings dialog "
                f"before running both at once."
            )
        except Exception:
            pass


class _FakeConfig:
    def __init__(self, udp_port):
        self.udp_port = udp_port


class _FakeListener:
    def __init__(self, udp_port, running):
        self.config = _FakeConfig(udp_port)
        self._running = running


class TestWarnUdpPortConflict:
    def test_warns_when_same_port_and_other_running(self, capsys):
        other = _FakeListener(2237, running=True)
        _warn_udp_port_conflict("WSJT-X", 2237, "MSHV", other, modal=False)
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "WSJT-X" in out and "MSHV" in out
        assert "2237" in out

    def test_no_warning_when_other_not_running(self, capsys):
        other = _FakeListener(2237, running=False)
        _warn_udp_port_conflict("WSJT-X", 2237, "MSHV", other, modal=False)
        assert capsys.readouterr().out == ""

    def test_no_warning_when_ports_differ(self, capsys):
        other = _FakeListener(2442, running=True)
        _warn_udp_port_conflict("WSJT-X", 2237, "MSHV", other, modal=False)
        assert capsys.readouterr().out == ""

    def test_no_warning_when_other_listener_is_none(self, capsys):
        _warn_udp_port_conflict("WSJT-X", 2237, "MSHV", None, modal=False)
        assert capsys.readouterr().out == ""

    def test_reverse_direction(self, capsys):
        """MSHV connecting while WSJT-X is already running on the same port."""
        other = _FakeListener(2237, running=True)
        _warn_udp_port_conflict("MSHV", 2237, "WSJT-X", other, modal=False)
        out = capsys.readouterr().out
        assert "MSHV" in out and "WSJT-X" in out
