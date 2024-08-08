import os
import logging
import numpy as np
import re
import cv2
import easyocr as easyocr
import pymupdf
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
from pdf_processing_image import process_image_based_page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the EasyOCR reader
easyocr_reader = easyocr.Reader(['en'], gpu=False)


# Function to get the Desktop folder path
def get_desktop_folder():
    if os.name == 'nt':  # For Windows
        return os.path.join(os.getenv('USERPROFILE'), 'Desktop/PdfAnalyzer')
    else:  # For macOS/Linux
        return os.path.join(os.path.expanduser('~'), 'Desktop/PdfAnalyzer')


# Define the output directory on the Desktop
DESKTOP_FOLDER = get_desktop_folder()
OUTPUT_FOLDER = os.path.join(DESKTOP_FOLDER, "output")
PROCESSING_PDFS_FOLDER = os.path.join(DESKTOP_FOLDER, "processing_pdfs")
CROPPED_IMAGES_FOLDER = os.path.join(DESKTOP_FOLDER, "cropped_images")

# Create directories if they don't exist
for folder in [OUTPUT_FOLDER, PROCESSING_PDFS_FOLDER, CROPPED_IMAGES_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)


def create_filtered_pdf(pdf_file, filter_type):
    logging.info(f"Starting to create filtered PDF for file: {pdf_file} with filter type: {filter_type}")

    reader = PdfReader(pdf_file)
    writer = PdfWriter()
    new_pdf_path = os.path.join(PROCESSING_PDFS_FOLDER, os.path.basename(pdf_file))
    logging.info(f"New filtered PDF will be saved to: {new_pdf_path}")

    # Create a sub-directory for the current PDF's cropped images
    pdf_name = os.path.splitext(os.path.basename(pdf_file))[0]
    pdf_cropped_images_folder = os.path.join(CROPPED_IMAGES_FOLDER, pdf_name)
    if not os.path.exists(pdf_cropped_images_folder):
        os.makedirs(pdf_cropped_images_folder)

    document = pymupdf.open(pdf_file)

    for page_num in range(len(reader.pages)):
        fitz_page = document.load_page(page_num)
        if image_has_bottom_right_pattern(fitz_page, page_num, pdf_cropped_images_folder):
            writer.add_page(reader.pages[page_num])
            logging.info(f"Page {page_num} added to filtered PDF.")
        else:
            logging.info(f"Page {page_num} does not match criteria and will not be added.")

    with open(new_pdf_path, 'wb') as out_pdf:
        writer.write(out_pdf)
    logging.info(f"Filtered PDF created successfully: {new_pdf_path}")

    return new_pdf_path


def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    # Apply dilation and erosion to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dilate = cv2.dilate(thresh, kernel, iterations=1)
    erode = cv2.erode(dilate, kernel, iterations=1)
    return erode


def image_has_bottom_right_pattern(fitz_page, page_num, pdf_cropped_images_folder):
    logging.info("Checking for image pattern in the bottom-right corner of the page.")

    # Define the region of interest (bottom-right 250x150 pixels)
    width, height = fitz_page.rect.width, fitz_page.rect.height
    box = pymupdf.Rect(width - 280, height - 150, width, height)

    # Render the selected region to an image
    pix = fitz_page.get_pixmap(clip=box)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Save the cropped image for debugging
    cropped_image_path = os.path.join(pdf_cropped_images_folder, f"cropped_page_{page_num}.png")
    image.save(cropped_image_path)
    logging.info(f"Cropped image saved for debugging: {cropped_image_path}")

    # Convert PIL image to numpy array
    image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    preprocessed_black = preprocess_image(image_np)

    # Convert back to PIL images
    preprocessed_black_pil_image = Image.fromarray(preprocessed_black)

    # Perform OCR with EasyOCR on all processed images
    ocr_result_preprocessed_black_easyocr = easyocr_reader.readtext(np.array(preprocessed_black_pil_image), detail=0)

    logging.debug(f"OCR result (preprocessed black) with EasyOCR: {ocr_result_preprocessed_black_easyocr}")

    # Extract text from EasyOCR results
    text_preprocessed_black_easyocr = ' '.join(ocr_result_preprocessed_black_easyocr)
    logging.info(f"Extracted text (preprocessed black) with EasyOCR: {text_preprocessed_black_easyocr}")
    match_preprocessed_black_easyocr = any(text.startswith('M') for text in ocr_result_preprocessed_black_easyocr)
    logging.info(f"OCR pattern found (preprocessed black) with EasyOCR: {match_preprocessed_black_easyocr}")

    return match_preprocessed_black_easyocr


def extract_most_bold_text(ocr_result):
    bold_text = ""
    max_boldness = -1
    for i in range(len(ocr_result['text'])):
        text = ocr_result['text'][i]
        if ('M' in text) and re.search(r'M', text):
            boldness = ocr_result['font'][i] if 'font' in ocr_result else 0  # Assuming font weight indicates boldness
            if boldness > max_boldness:
                bold_text = text
                max_boldness = boldness
    return bold_text


def process_pdf_file(pdf_file, output_file_path, progress_callback=None):
    logging.info(f"Starting to process PDF file: {pdf_file}")
    document = pymupdf.open(pdf_file)
    total_pages = len(document)
    logging.info(f"Total pages to process: {total_pages}")
    all_tables = []
    table_titles = []

    for page_num in range(total_pages):

        logging.info(f"Processing image-based page {page_num}.")
        tables, titles = process_image_based_page(pdf_file, page_num)

        all_tables.extend(tables)
        table_titles.extend(titles)

        # Emit progress update if a callback is provided
        if progress_callback:
            progress = int((page_num + 1) / total_pages * 100)
            progress_callback(progress)
            logging.info(f"Progress: {progress}%")

    save_all_tables_to_csv(all_tables, table_titles, output_file_path)
    logging.info(f"PDF processing complete. Tables saved to {output_file_path}")
    return f"Tables saved to {output_file_path}"


def save_all_tables_to_csv(tables, titles, output_file_path):
    logging.info("Saving all tables to CSV.")
    if not tables:
        logging.info("No tables found to save.")
        return

    with open(output_file_path, 'w', newline='') as f:
        for title, table in zip(titles, tables):
            f.write(f"{title}\n")
            table.to_csv(f, index=False)
            f.write("\n" + "-" * 50 + "\n")  # Add a dotted line between tables

    logging.info(f"All tables saved to {output_file_path}")


def extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, filter_type, progress_callback=None):
    logging.info(f"Extracting individual PDF: {pdf_file} with filter type: {filter_type}")
    base_file_name = os.path.basename(pdf_file).replace('.pdf', '')
    output_file_path = os.path.join(OUTPUT_FOLDER, f"{base_file_name}_tables.csv")
    logging.info(f"Output will be saved to: {output_file_path}")

    filtered_pdf = create_filtered_pdf(pdf_file, filter_type)
    message = process_pdf_file(filtered_pdf, output_file_path, progress_callback)
    extracted_tables[pdf_file] = message
    logging.info(f"Extraction complete for {pdf_file}.")


def process_all_pdfs(selected_files, extracted_tables, file_list_container, filter_type, progress_callback=None):
    logging.info(f"Starting to process all selected PDFs with filter type: {filter_type}")
    for index, pdf_file in enumerate(selected_files):
        logging.info(f"Processing file {index + 1}/{len(selected_files)}: {pdf_file}")
        extract_individual_pdf(pdf_file, index, extracted_tables, file_list_container, filter_type, progress_callback)
    logging.info("All selected PDFs processed.")
