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
    smaller = False
    for text in ocr_result_preprocessed_black_easyocr:
        logging.info(f"Checking text: {text}")

        # Determine if the text starts with "23"
        if text.startswith('23'):
            match = True
            logging.info("Match found: Text starts with '23'")

        try:
            # Take only the first two characters to check if it's smaller than 23
            number = int(text[:2])
            smaller = number < 23
            logging.info(f"Extracted number: {number}, smaller: {smaller}")
        except ValueError:
            logging.error(f"Failed to convert {text[:2]} to int.")
            smaller = False

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
    writer = PdfWriter()
    total_pages = len(reader.pages)
    fitz_document = pymupdf.open(pdf_file)
    logging.info(f"Total pages in the PDF: {total_pages}")

    # Initialize first and last index to the first and last pages of the PDF
    first_index = 0
    last_index = total_pages - 1

    # Perform binary search from the top
    first_index = binary_search_from_top(fitz_document, total_pages, first_index)

    # Perform binary search from the bottom
    last_index = binary_search_from_bottom(fitz_document, total_pages, last_index)

    logging.info(f"First page index with '23' pattern: {first_index}")
    logging.info(f"Last page index with '23' pattern: {last_index}")

    if first_index > last_index:
        logging.error("First index is greater than last index, something went wrong.")
        return None

    new_pdf_path = os.path.join(PROCESSING_PDFS_FOLDER,
                                f"{os.path.splitext(os.path.basename(pdf_file))[0]}_filtered_range.pdf")
    logging.info(f"New filtered PDF will be saved to: {new_pdf_path}")

    # Add pages between the found indices to the new PDF
    for page_num in range(first_index, last_index + 1):
        writer.add_page(reader.pages[page_num])
        if progress_callback:
            progress = int((page_num - first_index + 1) / (last_index - first_index + 1) * 100)
            progress_callback(progress)
            logging.info(f"Progress: {progress}%")

    with open(new_pdf_path, 'wb') as out_pdf:
        writer.write(out_pdf)
    logging.info(f"Filtered PDF created successfully between pages {first_index} and {last_index}: {new_pdf_path}")

    return new_pdf_path


def binary_search_from_top(fitz_document, total_pages, first_index):
    """Performs a binary search to find the first page matching the '23' pattern from the top."""
    low = first_index
    high = total_pages - 1
    found_index = -1  # Initialize with an invalid index

    while low <= high:
        mid = (low + high) // 2
        fitz_page = fitz_document.load_page(mid)
        match, smaller = spec_image_has_bottom_right_pattern(fitz_page, mid, '')

        if match:
            # If we find a match, we update the found_index and continue searching in the lower half
            found_index = mid
            high = mid - 1  # Continue searching towards the start to find the first occurrence

        elif smaller:
            low = mid + 1  # Continue searching from the current index upwards

        else:
            high = mid - 1  # Continue searching towards the start

    return found_index if found_index != -1 else first_index  # Return found_index or the initial index if not found


def binary_search_from_bottom(fitz_document, total_pages, last_index):
    """Performs a binary search to find the first page matching the '23' pattern from the bottom."""
    low = 0
    high = last_index
    found_index = -1  # Initialize with an invalid index

    while low <= high:
        mid = (low + high + 1) // 2
        fitz_page = fitz_document.load_page(mid)
        match, smaller = spec_image_has_bottom_right_pattern(fitz_page, mid, '')

        if match:
            found_index = mid
            low = mid + 1  # Continue searching upwards (towards the bottom)

        elif smaller:
            high = mid - 1  # Continue searching in the lower half (towards the top)

        else:
            high = mid - 1  # Continue searching in the lower half (towards the top)

    return found_index if found_index != -1 else last_index  # Return the found index or the initial last index
