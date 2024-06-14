import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QProgressBar, QLabel, QHBoxLayout,
    QTextEdit, QDesktopWidget
)
from PyQt5.QtCore import Qt
import PyPDF2


class PDFProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_files = []
        self.extracted_tables = {}

    def initUI(self):
        self.setWindowTitle("PDF Processor")

        # Set the window to 75% of the screen size
        screen_geometry = QDesktopWidget().availableGeometry()
        width = int(screen_geometry.width() * 0.75)
        height = int(screen_geometry.height() * 0.75)
        self.setGeometry(0, 0, width, height)
        self.move((screen_geometry.width() - width) // 2, (screen_geometry.height() - height) // 2)

        # Main layout
        self.layout = QVBoxLayout()

        # Instruction text widget
        self.instruction_label = QLabel("Click On Select File to process the PDF")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.instruction_label)

        # Container for file list and progress bars
        self.file_list_container = QVBoxLayout()
        self.layout.addLayout(self.file_list_container)

        # Buttons layout
        self.buttons_layout = QHBoxLayout()

        # Select PDF Files button
        self.select_button = QPushButton('Select PDF Files', self)
        self.select_button.clicked.connect(self.select_files)
        self.buttons_layout.addWidget(self.select_button)

        # Reset button
        self.reset_button = QPushButton('Reset', self)
        self.reset_button.clicked.connect(self.reset_selection)
        self.buttons_layout.addWidget(self.reset_button)

        # Extract All button
        self.extract_button = QPushButton('Extract All', self)
        self.extract_button.clicked.connect(self.process_all_pdfs)
        self.extract_button.setEnabled(False)
        self.buttons_layout.addWidget(self.extract_button)

        # Save All button
        self.save_button = QPushButton('Save All', self)
        self.save_button.clicked.connect(self.save_files)
        self.buttons_layout.addWidget(self.save_button)

        # Adding the buttons layout to the main layout
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

    def select_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)",
                                                options=options)
        if files:
            self.selected_files.extend(files)
            self.update_file_list_container()
        self.extract_button.setEnabled(bool(self.selected_files))

    def reset_selection(self):
        self.selected_files = []
        self.extracted_tables = {}
        self.update_file_list_container()
        self.extract_button.setEnabled(False)

    def save_files(self):
        if not self.selected_files:
            QMessageBox.warning(self, "No files selected", "Please select PDF files to save.")
            return

        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(self, "Save All PDFs", "", "PDF Files (*.pdf);;All Files (*)",
                                                   options=options)
        if save_path:
            with open(save_path, 'wb') as output_pdf:
                pdf_writer = PyPDF2.PdfWriter()
                for pdf_file in self.selected_files:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page_num in range(len(pdf_reader.pages)):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                pdf_writer.write(output_pdf)
            QMessageBox.information(self, "Saved", f"Files saved to {save_path}")

    def process_all_pdfs(self):
        if not self.selected_files:
            QMessageBox.warning(self, "No files selected", "Please select PDF files to extract.")
            return

        for index, pdf_file in enumerate(self.selected_files):
            self.process_pdf(pdf_file, index)

    def process_pdf(self, pdf_file, index):
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        progress_bar = self.file_list_container.itemAt(index * 3).layout().itemAt(1).widget()

        extracted_text = ""
        for page_num in range(num_pages):
            # Simulate processing each page
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text() + "\n"  # Here you can handle the extracted text

            # Update progress bar
            progress = int((page_num + 1) / num_pages * 100)
            progress_bar.setValue(progress)

        # Save extracted text for preview
        self.extracted_tables[pdf_file] = extracted_text

    def update_file_list_container(self):
        for i in reversed(range(self.file_list_container.count())):
            widget_to_remove = self.file_list_container.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        for index, file in enumerate(self.selected_files):
            file_layout = QHBoxLayout()
            file_label = QLabel(file)
            file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_layout.addWidget(file_label)

            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            file_layout.addWidget(progress_bar)

            container_widget = QWidget()
            container_widget.setLayout(file_layout)
            self.file_list_container.addWidget(container_widget)

            # Buttons for extracting, previewing, and saving extracted tables
            buttons_layout = QHBoxLayout()

            extract_button = QPushButton('Extract')
            extract_button.clicked.connect(lambda checked, f=file, i=index: self.process_pdf(f, i))
            buttons_layout.addWidget(extract_button)

            preview_button = QPushButton('Preview Extracted Tables')
            preview_button.clicked.connect(lambda checked, f=file: self.preview_extracted_tables(f))
            buttons_layout.addWidget(preview_button)

            save_button = QPushButton('Save Extracted Tables')
            save_button.clicked.connect(lambda checked, f=file: self.save_extracted_tables(f))
            buttons_layout.addWidget(save_button)

            buttons_widget = QWidget()
            buttons_widget.setLayout(buttons_layout)
            self.file_list_container.addWidget(buttons_widget)

    def preview_extracted_tables(self, file):
        if file in self.extracted_tables:
            extracted_text = self.extracted_tables[file]
            preview_window = QWidget()
            preview_window.setWindowTitle("Preview Extracted Tables")
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(extracted_text)
            layout.addWidget(text_edit)
            preview_window.setLayout(layout)
            preview_window.show()
        else:
            QMessageBox.warning(self, "No extraction available", "Please extract data before previewing.")

    def save_extracted_tables(self, file):
        if file in self.extracted_tables:
            extracted_text = self.extracted_tables[file]
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Extracted Tables", "",
                                                       "Text Files (*.txt);;All Files (*)", options=options)
            if save_path:
                with open(save_path, 'w') as f:
                    f.write(extracted_text)
                QMessageBox.information(self, "Saved", f"Extracted tables saved to {save_path}")
        else:
            QMessageBox.warning(self, "No extraction available", "Please extract data before saving.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFProcessor()
    ex.show()
    sys.exit(app.exec_())
