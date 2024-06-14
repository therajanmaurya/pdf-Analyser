import fitz  # PyMuPDF
import logging
import os
import pandas as pd
from pdf_processing_text import process_text_based_page
from pdf_processing_image import process_image_based_page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the output directory relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output")


def process_pdf_file(pdf_file, output_file_path, progress_callback=None):
    document = fitz.open(pdf_file)
    total_pages = len(document)
    all_tables = []
    table_titles = []

    for page_num in range(total_pages):
        page = document.load_page(page_num)
        text = page.get_text("text")

        if text.strip():  # Text-based page
            tables, titles = process_text_based_page(pdf_file, page_num)
            all_tables.extend(tables)
            table_titles.extend(titles)
        else:  # Image-based page
            tables, titles = process_image_based_page(pdf_file, page_num)
            all_tables.extend(tables)
            table_titles.extend(titles)

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
            f.write("\n" + "-" * 50 + "\n")  # Add a dotted line between tables

    logging.info(f"All tables saved to {output_file_path}")


def extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, progress_callback=None):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    base_file_name = os.path.basename(pdf_file).replace('.pdf', '')
    output_file_path = os.path.join(OUTPUT_FOLDER, f"{base_file_name}_tables.csv")
    logging.info(f"Processing file: {pdf_file}")
    logging.info(f"Output will be saved to: {output_file_path}")
    message = process_pdf_file(pdf_file, output_file_path, progress_callback)
    extracted_tables[pdf_file] = message


def process_all_pdfs(selected_files, extracted_tables, file_list_container, progress_callback=None):
    for index, pdf_file in enumerate(selected_files):
        extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, progress_callback)
