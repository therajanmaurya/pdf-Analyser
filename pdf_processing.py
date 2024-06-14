import camelot
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import re
import logging
import pandas as pd
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def ocr_image(image):
    return pytesseract.image_to_string(image)


def contains_schedule_title(text):
    return re.search(r'schedule', text, re.IGNORECASE) is not None


def extract_tables_from_image_text(text):
    # Simple method to parse and extract tables from OCR text
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


def process_pdf_file(pdf_file, output_file_path, progress_callback=None):
    document = fitz.open(pdf_file)
    total_pages = len(document)
    all_tables = []
    table_titles = []

    for page_num in range(total_pages):
        page = document.load_page(page_num)
        text = page.get_text("text")

        if text.strip():  # Text-based page
            tables = camelot.read_pdf(pdf_file, pages=str(page_num + 1))
            if tables:
                for table_num, table in enumerate(tables):
                    table_text = table.df.to_string(index=False)
                    if contains_schedule_title(table_text):
                        logging.info(f"Page {page_num + 1} is text-based and contains a schedule table.")
                        all_tables.append(table.df)
                        table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
            else:
                logging.info(f"Page {page_num + 1} is text-based but does not contain schedule tables.")
        else:  # Image-based page
            image = page.get_pixmap()
            image_data = Image.frombytes("RGB", [image.width, image.height], image.samples)
            ocr_text = ocr_image(image_data)
            if contains_schedule_title(ocr_text):  # Use OCR to extract tables from text
                logging.info(f"Page {page_num + 1} is image-based and contains a schedule table.")
                extracted_tables = extract_tables_from_image_text(ocr_text)
                for table_num, table in enumerate(extracted_tables):
                    all_tables.append(table)
                    table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
            else:
                logging.info(f"Page {page_num + 1} is image-based but does not contain schedule tables.")

        # Emit progress update if a callback is provided
        if progress_callback:
            progress = int((page_num + 1) / total_pages * 100)
            progress_callback(progress)

    save_all_tables_to_csv(all_tables, table_titles, output_file_path)
    return f"Tables saved to {output_file_path}"


def save_all_tables_to_csv(tables, titles, output_file_path):
    if not tables:
        logging.info("No tables found to save.")
        return
    with open(output_file_path, 'w', newline='') as f:
        for title, table in zip(titles, tables):
            f.write(f"{title}\n")
            table.to_csv(f, index=False)
            f.write("\n")
    logging.info(f"All tables saved to {output_file_path}")


def extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, progress_callback=None):
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    base_file_name = os.path.basename(pdf_file).replace('.pdf', '')
    output_file_path = os.path.join(output_folder, f"{base_file_name}_tables.csv")
    message = process_pdf_file(pdf_file, output_file_path, progress_callback)
    extracted_tables[pdf_file] = message


def process_all_pdfs(selected_files, extracted_tables, file_list_container, progress_callback=None):
    for index, pdf_file in enumerate(selected_files):
        extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, progress_callback)
