# main.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['BruckerCo.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'frontend',  # Add any additional hidden imports here
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter', 'pathlib',  # Exclude unnecessary modules
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BruckerCo_Windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    name='BruckerCo_Windows'
)
