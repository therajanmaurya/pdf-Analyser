from PyQt5.QtWidgets import QMessageBox, QTextEdit, QVBoxLayout, QWidget, QFileDialog


def preview_extracted_tables(pdf_file, extracted_tables):
    if pdf_file in extracted_tables:
        extracted_text = extracted_tables[pdf_file]
        preview_window = QWidget()
        preview_window.setWindowTitle("Preview Extracted Tables")
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(extracted_text)
        layout.addWidget(text_edit)
        preview_window.setLayout(layout)
        preview_window.show()
    else:
        QMessageBox.warning(None, "No extraction available", "Please extract data before previewing.")


def save_extracted_tables(pdf_file, extracted_tables):
    if pdf_file in extracted_tables:
        extracted_text = extracted_tables[pdf_file]
        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Extracted Tables", "",
                                                   "Text Files (*.txt);;All Files (*)", options=options)
        if save_path:
            with open(save_path, 'w') as f:
                f.write(extracted_text)
            QMessageBox.information(None, "Saved", f"Extracted tables saved to {save_path}")
    else:
        QMessageBox.warning(None, "No extraction available", "Please extract data before saving.")
