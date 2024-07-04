# main.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_extraction.py', 'pdf_processing_image.py', 'pdf_processing_text.py', 'pdf_processing.py', 'pdf_processor.py', 'pdf_saving.py'],
    pathex=['.'],  # Ensure this is set to the relative path
    binaries=[],
    datas=[],
    hiddenimports=[
        'pdfplumber',
        'pandas',
        'tk',
        'PyQt5',
        'camelot',
        'PyPDF2',
        'opencv-python',
        'PyMuPDF',
        'pytesseract',
        'openai',
        'Pillow',
        'opencv-python-headless',
        'fitz'
        'frontend'
    ],
    hookspath=[],
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
    [],
    exclude_binaries=True,
    name='pdf_tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    name='pdf_tool'
)
