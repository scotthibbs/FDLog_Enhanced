# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for FDLog_Enhanced
# Build with: pyinstaller FDLog_Enhanced.spec

block_cipher = None

from PyInstaller.utils.hooks import collect_all

# Collect upnpclient and all its dependencies (lazy import — static analysis misses them)
_upnp_datas, _upnp_bins, _upnp_hidden = collect_all('upnpclient')
_ifaddr_datas, _ifaddr_bins, _ifaddr_hidden = collect_all('ifaddr')
_lxml_datas, _lxml_bins, _lxml_hidden = collect_all('lxml')
_req_datas, _req_bins, _req_hidden = collect_all('requests')
_dateutil_datas, _dateutil_bins, _dateutil_hidden = collect_all('dateutil')
_charset_datas, _charset_bins, _charset_hidden = collect_all('charset_normalizer')
_ws_datas, _ws_bins, _ws_hidden = collect_all('websockets')

# Data files to include (source, destination folder)
data_files = [
    ('Arrl_sections_ref.txt', '.'),
    ('ARRL_Band_Plans.txt', '.'),
    ('logcaptain.txt', '.'),
    ('Keyhelp.txt', '.'),
    ('Releaselog.txt', '.'),
    ('README.txt', '.'),
    ('README.md', '.'),
    ('License.txt', '.'),
    ('NTS_eg.txt', '.'),
    ('Bands.pdf', '.'),
    ('Rules.pdf', '.'),
    ('W1AW.pdf', '.'),
    ('parser.py', '.'),
    ('cty.dat', '.'),
    ('FDLog Icon.ico', '.'),
    ('FDLog Icon.png', '.'),
]

a = Analysis(
    ['FDLog_Enhanced.py'],
    pathex=[],
    binaries=[] + _upnp_bins + _ifaddr_bins + _lxml_bins + _req_bins + _dateutil_bins + _charset_bins + _ws_bins,
    datas=data_files + _upnp_datas + _ifaddr_datas + _lxml_datas + _req_datas + _dateutil_datas + _charset_datas + _ws_datas,
    hiddenimports=[
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'cw_keying',
        'parser',
        'websockets.sync.server',
        'websockets.sync.client',
    ] + _upnp_hidden + _ifaddr_hidden + _lxml_hidden + _req_hidden + _dateutil_hidden + _charset_hidden + _ws_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # pandas/plotly no longer used (WAS map is pure Tkinter) - excluded so
    # nothing pulls them back in. numpy stays: voice recording uses it, and
    # voice_keying checks the CPU (IsProcessorFeaturePresent) BEFORE
    # importing it so old CPUs skip it instead of fail-fasting. 04Jul2026
    # cryptography/bcrypt/paramiko/nacl/OpenSSL: only reachable via requests'
    # OPTIONAL try-imports (requests.help, urllib3.contrib.pyopenssl) when
    # they happen to be installed in the build Python (+9MB for nothing).
    # requests uses the stdlib ssl module without them. Excluding keeps the
    # exe size the same no matter which Python builds it. 04Jul2026
    # pytest & friends ride in via numpy.testing's optional imports; PIL via
    # pygments; bs4/soupsieve via lxml.html.soupparser's optional import;
    # werkzeug similar. All dead weight at runtime.
    excludes=['pandas', 'plotly', 'cryptography', 'bcrypt', 'paramiko',
              'nacl', 'OpenSSL',
              'pytest', '_pytest', 'pluggy', 'iniconfig', 'pygments',
              'PIL', 'bs4', 'soupsieve', 'werkzeug'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FDLog_Enhanced',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for startup prompts
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None if __import__('sys').platform == 'darwin' else 'FDLog Icon.ico',
)
