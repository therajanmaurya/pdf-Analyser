import camelot
import logging
import re


def contains_schedule_title(text):
    return re.search(r'schedule', text, re.IGNORECASE) is not None


def process_text_based_page(pdf_file, page_num):
    tables = camelot.read_pdf(pdf_file, pages=str(page_num + 1))
    extracted_tables = []
    table_titles = []

    if tables:
        for table_num, table in enumerate(tables):
            table_text = table.df.to_string(index=False)
            if contains_schedule_title(table_text):
                logging.info(f"Page {page_num + 1} is text-based and contains a schedule table.")
                extracted_tables.append(table.df)
                table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
    else:
        logging.info(f"Page {page_num + 1} is text-based but does not contain schedule tables.")

    return extracted_tables, table_titles
