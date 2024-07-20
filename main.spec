# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['BruckerCo.py'],
    pathex=['/mnt/data/'],
    binaries=[],
    datas=[
        ('pdf_extraction.py', '.'),
        ('pdf_processing_image.py', '.'),
        ('pdf_processing_text.py', '.'),
        ('pdf_processing.py', '.'),
        ('pdf_processor.py', '.'),
        ('pdf_saving.py', '.')
    ],
    hiddenimports=['pandas', 'PyQt5', 'setuptools', 'PyPDF2', 'cv2', 'fitz', 'pytesseract', 'PIL', 'numpy', 'configparser', 'attrs', 'cryptography', 'filelock', 'easyocr'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name='BruckerCo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='BruckerCo'
)
