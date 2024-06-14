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
                logging.info(f"Extracted table {table_num + 1} from Page {page_num + 1}:\n{table.df}")
                print(f"Extracted table {table_num + 1} from Page {page_num + 1}:\n{table.df}\n")
                extracted_tables.append(table.df)
                table_titles.append(f"Table {table_num + 1} on Page {page_num + 1}")
            else:
                logging.info(f"Page {page_num + 1} contains text but does not have a schedule table.")
    else:
        logging.info(f"Page {page_num + 1} is text-based but does not contain any tables.")

    return extracted_tables, table_titles
