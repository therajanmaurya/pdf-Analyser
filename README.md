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
python BruckerCo.py
```

## Possible Regex

```sh
`M\d+\.\d+` Example: M2.1
`M-\d{3}` Example: M-001
`M\d+\.\d{2}` Example: M1.01
`M\d+-\d{3}` Example: M1-100
`M-\d+\.\d+` Example: M-1.0
`M\d{3}` Example: M001
`M[a-zA-Z]\d+\.\d+` Example: ME1.1
`M\d{1,2}-\d{2}` Example: M1-25
```

## Building the Executable
To generate an executable (.exe) file for Windows, follow these steps:

- Install PyInstaller:
```sh
pip install pyinstaller
```

- Navigate to your project directory:
```sh
cd path\to\your\project
```

- Run PyInstaller:
```sh
pyinstaller --onefile BruckerCo.py
```

- Locate the executable:
After PyInstaller finishes, you'll find your executable in the dist directory inside your project folder:
```sh
pdf_analyzer\dist\main.exe
```

Additional PyInstaller Options
You can customize the executable with additional options:

--icon=icon.ico: To add an icon to your executable.
--add-data 'src;dest': To add non-Python files (e.g., data files).
--noconsole: To disable the console window (useful for GUI applications).

```sh
# Activate your virtual environment if not already active
source myenv/bin/activate  # On macOS/Linux
myenv\Scripts\activate  # On Windows
python -m venv venv

# Basic command
pyinstaller --onefile BruckerCo.py

# With an icon and additional options
pyinstaller --onefile --icon=logo.ico --hidden-import=module1 --hidden-import=module2 BruckerCo.py

# Using UPX (ensure UPX is installed and path is correct)
pyinstaller --onefile --icon=myicon.ico --strip BruckerCo.py
```

## Features

- Extracts tables from PDF files and saves them as CSV files.
- Provides a simple UI for selecting multiple PDF files.
- Displays a progress bar for each PDF file being processed.