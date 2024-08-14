import os
import logging
import numpy as np
import re
import cv2
import easyocr
import pymupdf
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image

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


def create_filtered_pdf(pdf_file, filter_type, progress_callback=None):
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
    total_pages = len(reader.pages)

    for page_num in range(total_pages):
        fitz_page = document.load_page(page_num)
        if image_has_bottom_right_pattern(fitz_page, page_num, pdf_cropped_images_folder, filter_type):
            writer.add_page(reader.pages[page_num])
            logging.info(f"Page {page_num} added to filtered PDF.")
        else:
            logging.info(f"Page {page_num} does not match criteria and will not be added.")

        if progress_callback:
            progress = int((page_num + 1) / total_pages * 100)
            progress_callback(progress)
            logging.info(f"Progress: {progress}%")

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


def image_has_bottom_right_pattern(fitz_page, page_num, pdf_cropped_images_folder, filter_type):
    logging.info("Checking for image pattern in the page.")

    if filter_type == "PLANS":
        # Define the region of interest (bottom-right 250x150 pixels)
        width, height = fitz_page.rect.width, fitz_page.rect.height
        box = pymupdf.Rect(width - 280, height - 150, width, height)
    elif filter_type == "SPECIFICATIONS":
        # Define the region of interest as double the region of width and height
        width, height = fitz_page.rect.width, fitz_page.rect.height
        box = pymupdf.Rect(width - 300, height - 200, width, height)

    # Render the selected region to an image at higher resolution
    zoom = 2  # Adjust zoom to increase resolution
    mat = pymupdf.Matrix(zoom, zoom)
    pix = fitz_page.get_pixmap(matrix=mat, clip=box)
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

    if filter_type == "PLANS":
        match = any(text.startswith('M') for text in ocr_result_preprocessed_black_easyocr)
    elif filter_type == "SPECIFICATIONS":
        match = any(text.startswith('23') for text in ocr_result_preprocessed_black_easyocr)

    logging.info(f"OCR pattern found with EasyOCR: {match}")

    return match


def spec_image_has_bottom_right_pattern(fitz_page, page_num, pdf_cropped_images_folder):
    logging.info("Checking for image pattern in the page.")

    # Define the region of interest as double the region of width and height for specifications
    width, height = fitz_page.rect.width, fitz_page.rect.height
    box = pymupdf.Rect(width - 300, height - 200, width, height)

    # Render the selected region to an image at higher resolution
    zoom = 2  # Adjust zoom to increase resolution
    mat = pymupdf.Matrix(zoom, zoom)
    pix = fitz_page.get_pixmap(matrix=mat, clip=box)
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

    # Extract text from EasyOCR results and log it
    text_preprocessed_black_easyocr = ' '.join(ocr_result_preprocessed_black_easyocr)
    logging.info(f"Extracted text (preprocessed black) with EasyOCR: {text_preprocessed_black_easyocr}")

    match = False
    match_text = ""
    for text in ocr_result_preprocessed_black_easyocr:
        logging.info(f"Checking text: {text}")

        if text.startswith('2'):
            match_text = text

        # Determine if the text starts with "23"
        if text.startswith('23'):
            match = True
            match_text = text
            logging.info("Match found: Text starts with '23'")
            break

    try:
        # Take only the first two characters to check if it's smaller than 23
        number = int(match_text[:2])
        smaller = number < 23
        logging.info(f"Extracted number: {number}, smaller: {smaller}")
    except ValueError:
        logging.error(f"Failed to convert {match_text[:2]} to int.")
        smaller = None

    logging.info(f"OCR pattern found with EasyOCR: {match}, smaller: {smaller}")

    # Delete the cropped image after processing
    try:
        os.remove(cropped_image_path)
        logging.info(f"Cropped image deleted: {cropped_image_path}")
    except Exception as e:
        logging.error(f"Error deleting cropped image: {cropped_image_path}. Error: {e}")

    return match, smaller


def create_pdf_between_indices(pdf_file, progress_callback=None):
    logging.info(f"Starting to create PDF between indices for file: {pdf_file}")

    # Load the PDF and initialize variables
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)
    fitz_document = pymupdf.open(pdf_file)
    logging.info(f"Total pages in the PDF: {total_pages}")

    first_index = 0
    last_index = total_pages - 1

    # Perform binary search to find the first matching index
    first_match_index = binary_search_from_top(fitz_document, total_pages, 0)

    if first_match_index == 0:
        logging.error("No matching page found.")
        return None

    logging.info(f"First matching page index with '23' pattern: {first_match_index}")

    # Add pages upward from first_match_index until a page with a smaller number than '23' is found
    for page_num in range(first_match_index, -1, -1):
        fitz_page = fitz_document.load_page(page_num)
        match, smaller = spec_image_has_bottom_right_pattern(fitz_page, page_num, '')

        if match:
            logging.info(f"Page {page_num} match - '23'")
            first_index = page_num
        elif smaller is None:
            logging.info(f"Page {page_num} has an undefined 'smaller' value, skipping page.")
            continue
        elif smaller:
            first_index = page_num
            logging.info(f"Page {page_num} has a smaller value, stopping upward search.")
            break

    # Add pages from first_match_index downwards until a page with a number greater than or equal to '23' is found
    for page_num in range(first_match_index + 1, total_pages):
        fitz_page = fitz_document.load_page(page_num)
        match, smaller = spec_image_has_bottom_right_pattern(fitz_page, page_num, '')

        if match:
            logging.info(f"Page {page_num} match - '23'")
            last_index = page_num
        elif smaller is None:
            logging.info(f"Page {page_num} has an undefined 'smaller' value, skipping page.")
            continue
        elif not smaller:
            last_index = page_num
            logging.info(f"Page {page_num} has a smaller value, stopping downward search.")
            break

    # Create a new PDF with pages from first_index to last_index
    new_pdf_path = os.path.join(PROCESSING_PDFS_FOLDER,
                                f"{os.path.splitext(os.path.basename(pdf_file))[0]}_filtered_range.pdf")
    logging.info(f"New filtered PDF will be saved to: {new_pdf_path}")

    writer = PdfWriter()
    for page_num in range(first_index, last_index + 1):
        writer.add_page(reader.pages[page_num])

    # Write the final filtered PDF
    with open(new_pdf_path, 'wb') as out_pdf:
        writer.write(out_pdf)
    logging.info(f"Filtered PDF created successfully from pages {first_index} to {last_index}: {new_pdf_path}")

    return new_pdf_path


def binary_search_from_top(fitz_document, total_pages, first_index):
    """Performs a binary search to find the first page matching the '23' pattern from the top."""
    low = first_index
    high = total_pages - 1
    found_index = -1  # Initialize with an invalid index

    while low <= high:
        mid = (low + high) // 2
        logging.info(f"binary_search_from_top -> Low: {low}, High: {high}, Mid: {mid}, Found Index: {found_index}")

        fitz_page = fitz_document.load_page(mid)
        match, smaller = spec_image_has_bottom_right_pattern(fitz_page, mid, '')

        if match:
            # If we find a match, we update the found_index and continue searching in the lower half
            found_index = mid
            return mid

        if smaller:
            low = mid + 1  # Continue searching from the current index upwards
        elif not smaller:
            high = mid - 1
        elif smaller is None:
            low = low + 1

    logging.info(
        f"binary_search_from_top Final Found Index from top: {found_index}, returning: {found_index if found_index != -1 else first_index}")
    return found_index if found_index != -1 else first_index  # Return found_index or the initial index if not found
