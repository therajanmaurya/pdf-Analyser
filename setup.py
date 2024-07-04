from setuptools import setup, find_packages

setup(
    name='BruckerCo',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'pdfplumber~=0.11.1',
        'pandas~=2.2.2',
        'tk',
        'PyQt5~=5.15.10',
        'setuptools~=68.2.0',
        'camelot-py[cv]',
        'PyQt5',
        'PyPDF2~=3.0.1',
        'opencv-python',
        'PyMuPDF',
        'pytesseract~=0.3.10',
        'openai~=0.27.0',
        'Pillow==10.0.1',
        'opencv-python-headless==4.10.0.82',
        'fitz~=0.0.1.dev2',
        'pyinstaller'
    ],
    entry_points={
        'console_scripts': [
            'bruckercopy = BruckerCo:main',
        ],
    },
)
