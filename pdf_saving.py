import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def save_all_pdfs(selected_files):
    if not selected_files:
        QMessageBox.warning(None, "No files selected", "Please select PDF files to save.")
        return

    options = QFileDialog.Options()
    save_path, _ = QFileDialog.getSaveFileName(None, "Save All PDFs", "", "PDF Files (*.pdf);;All Files (*)",
                                               options=options)
    if save_path:
        with open(save_path, 'wb') as output_pdf:
            pdf_writer = PdfWriter()
            for pdf_file in selected_files:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            pdf_writer.write(output_pdf)
        QMessageBox.information(None, "Saved", f"Files saved to {save_path}")
