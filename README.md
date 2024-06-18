# PDF Analyzer

This project is a PDF Analyzer tool that extracts tables from PDF files and saves them as CSV files. It provides a simple user interface for selecting multiple PDF files and shows a progress bar for the processing of each PDF file.

## Requirements

- Python 3.x
- pdfplumber
- pandas
- tkinter

## Installation

1. Clone the repository.
2. Install the required dependencies using:

```sh
pip install -r requirements.txt
```

## Usage

Run the `main.py` file to start the application:

```sh
python main.py
```

## Possible Regex

```sh
`M\d+\.\d+` Example: M2.1
`M-\d{3}` Example: M-001
`M\d+\.\d{2}` Example: M1.01
`M\d+-\d{3}` Example: M1-100
`M-\d+\.\d+` Example: M-1.0
`M\d{3}` Example: M001
```

## Features

- Extracts tables from PDF files and saves them as CSV files.
- Provides a simple UI for selecting multiple PDF files.
- Displays a progress bar for each PDF file being processed.