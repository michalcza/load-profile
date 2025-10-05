# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Hidden imports for scientific/plotting stacks
hidden = (
    collect_submodules("pandas")
    + collect_submodules("plotly")
    + collect_submodules("bokeh")
    + collect_submodules("matplotlib")
)

a = Analysis(
    ['lpd-gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Embed the secondary scripts so the GUI can execute them in-process.
        ('lpd-main.py', '.'),
        ('lpd-interactive.py', '.'),
        ('lpd-merge.py', '.'),
        ('lpd-weather.py', '.'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={
        # Keep matplotlib backend set minimal to avoid noisy test backends
        "matplotlib": {"backends": ["Agg"]}
    },
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
    name='lpd-suite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed GUI
    disable_windowed_traceback=False,
)
