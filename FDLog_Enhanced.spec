# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for FDLog_Enhanced
# Build with: pyinstaller FDLog_Enhanced.spec

block_cipher = None

# Data files to include (source, destination folder)
data_files = [
    ('Arrl_sections_ref.txt', '.'),
    ('ARRL_Band_Plans.txt', '.'),
    ('Manual.txt', '.'),
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
]

a = Analysis(
    ['FDLog_Enhanced.py'],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'pandas',
        'plotly',
        'plotly.express',
        'plotly.graph_objects',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'cw_keying',
        'parser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    icon=None,  # Add icon path here if you have one: icon='fdlog.ico'
)
