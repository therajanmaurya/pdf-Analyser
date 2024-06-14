import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import logging
import pandas as pd
import re


def ocr_image(image):
    return pytesseract.image_to_string(image)


def contains_schedule_title(text):
    return re.search(r'schedule', text, re.IGNORECASE) is not None


def extract_tables_from_image_text(text):
    tables = []
    lines = text.split('\n')
    table = []
    for line in lines:
        if contains_schedule_title(line):
            table.append(line)
        elif table:
            tables.append(table)
            table = []
    if table:
        tables.append(table)

    extracted_tables = []
    for table in tables:
        table_df = pd.DataFrame([x.split() for x in table])
        extracted_tables.append(table_df)
    return extracted_tables


def process_image_based_page(pdf_file, page_num):
    document = fitz.open(pdf_file)
    page = document.load_page(page_num)
    image = page.get_pixmap()
    image_data = Image.frombytes("RGB", [image.width, image.height], image.samples)
    ocr_text = ocr_image(image_data)

    extracted_tables = []
    table_titles = []

    if contains_schedule_title(ocr_text):
        logging.info(f"Page {page_num + 1} is image-based and contains a schedule table.")
        extracted_tables = extract_tables_from_image_text(ocr_text)
        for table_num, table in enumerate(extracted_tables):
            table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
    else:
        logging.info(f"Page {page_num + 1} is image-based but does not contain schedule tables.")

    return extracted_tables, table_titles
