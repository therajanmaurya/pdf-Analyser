import cv2
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import logging
import pandas as pd
import re
import os


def ocr_image(image):
    return pytesseract.image_to_string(image)


def contains_schedule_title(text):
    return re.search(r'schedule', text, re.IGNORECASE) is not None


def detect_tables_in_image(image_path):
    image = cv2.imread(image_path, 0)  # Read the image in grayscale
    blur = cv2.GaussianBlur(image, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out contours that do not resemble a table structure
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 50:  # Adjust these dimensions as needed for your table size
            return True  # A table-like structure is detected
    return False


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
    try:
        document = fitz.open(pdf_file)
        page = document.load_page(page_num)
        pix = page.get_pixmap()
        image_path = f"page_{page_num}.png"
        pix.save(image_path)

        if detect_tables_in_image(image_path):
            logging.info(f"Page {page_num + 1} is image-based and contains a table structure.")
            image = Image.open(image_path)
            ocr_text = ocr_image(image)
            extracted_tables = extract_tables_from_image_text(ocr_text)

            table_titles = []
            for table_num, table in enumerate(extracted_tables):
                table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
            return extracted_tables, table_titles
        else:
            logging.info(f"Page {page_num + 1} is image-based but does not contain table structures.")
            return [], []
    except Exception as e:
        logging.error(f"Error processing page {page_num + 1}: {e}")
        return [], []


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    pdf_file = "example.pdf"
    page_num = 0

    if not os.path.exists(pdf_file):
        logging.error(f"PDF file '{pdf_file}' does not exist.")
    else:
        extracted_tables, table_titles = process_image_based_page(pdf_file, page_num)
        for title, table in zip(table_titles, extracted_tables):
            print(f"{title}\n{table}\n")
