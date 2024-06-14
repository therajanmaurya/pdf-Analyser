from setuptools import setup

setup(
    name="pdf_analyzer",
    version="1.0",
    description="PDF Analyzer to extract tables from PDFs and save as CSV",
    author="Your Name",
    packages=["."],
    install_requires=[
        "pdfplumber",
        "pandas",
        "tk"
    ],
    entry_points={
        "console_scripts": [
            "pdf_analyzer = main:main"
        ]
    }
)
