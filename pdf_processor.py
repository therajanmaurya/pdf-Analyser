from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QProgressBar, QDesktopWidget, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import logging
import os
from pdf_processing import extract_individual_pdf, process_all_pdfs, create_filtered_pdf
from pdf_saving import save_all_pdfs
from pdf_extraction import preview_extracted_tables, save_extracted_tables

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PDFProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_files = []
        self.extracted_tables = {}
        self.progress_bars = []

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
        self.extract_button.clicked.connect(self.extract_all_pdfs)
        self.extract_button.setEnabled(False)
        self.buttons_layout.addWidget(self.extract_button)

        # Save All button
        self.save_button = QPushButton('Save All', self)
        self.save_button.clicked.connect(self.save_all_pdfs)
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
            self.instruction_label.setText("Work in progress")
            logging.info(f"Selected files: {self.selected_files}")
        self.extract_button.setEnabled(bool(self.selected_files))

    def reset_selection(self):
        self.selected_files = []
        self.extracted_tables = {}
        self.progress_bars = []
        self.update_file_list_container()
        self.extract_button.setEnabled(False)
        self.instruction_label.setText("Click On Select File to process the PDF")
        logging.info("Selection reset")

    def save_all_pdfs(self):
        save_all_pdfs(self.selected_files)

    def extract_all_pdfs(self):
        self.thread = QThread()
        self.worker = ExtractWorker(self.selected_files, self.extracted_tables, self.file_list_container)
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()
        logging.info("Started extracting all PDFs")

    def update_file_list_container(self):
        for i in reversed(range(self.file_list_container.count())):
            widget_to_remove = self.file_list_container.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        self.progress_bars = []
        for index, file in enumerate(self.selected_files):
            file_layout = QHBoxLayout()

            # Create alias for the file
            alias = os.path.basename(file)

            file_label = QLabel(alias)
            file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_label.setToolTip(file)  # Show full path on hover
            file_layout.addWidget(file_label)

            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            file_layout.addWidget(progress_bar)
            self.progress_bars.append(progress_bar)

            container_widget = QWidget()
            container_widget.setLayout(file_layout)
            self.file_list_container.addWidget(container_widget)

            # Buttons for extracting, previewing, and saving extracted tables
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(0)  # Remove spacing between buttons and progress bar

            extract_button = QPushButton('Extract')
            extract_button.clicked.connect(lambda checked, f=file, i=index: self.extract_pdf(f, i))
            buttons_layout.addWidget(extract_button)

            preview_button = QPushButton('Preview Extracted Tables')
            preview_button.clicked.connect(lambda checked, f=file: preview_extracted_tables(f, self.extracted_tables))
            buttons_layout.addWidget(preview_button)

            save_button = QPushButton('Save Extracted Tables')
            save_button.clicked.connect(lambda checked, f=file: save_extracted_tables(f, self.extracted_tables))
            buttons_layout.addWidget(save_button)

            buttons_widget = QWidget()
            buttons_widget.setLayout(buttons_layout)
            self.file_list_container.addWidget(buttons_widget)

    def extract_pdf(self, file, index):
        self.thread = QThread()
        self.worker = ExtractWorker([file], self.extracted_tables, self.file_list_container, index)
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()
        logging.info(f"Started extracting PDF: {file}")

    def update_progress(self, index, progress):
        progress_bar = self.progress_bars[index]
        progress_bar.setValue(progress)
        logging.info(f"Progress for file {index}: {progress}%")


class ExtractWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()

    def __init__(self, files, extracted_tables, file_list_container, index=None):
        super().__init__()
        self.files = files
        self.extracted_tables = extracted_tables
        self.file_list_container = file_list_container
        self.index = index

    def run(self):
        if self.index is not None:
            self.extract_single_file(self.files[0], self.index)
        else:
            for index, file in enumerate(self.files):
                self.extract_single_file(file, index)
        self.finished.emit()

    def extract_single_file(self, file, index):
        def progress_callback(progress):
            self.progress.emit(index, progress)

        filtered_pdf = create_filtered_pdf(file)
        extract_individual_pdf(filtered_pdf, index, self.extracted_tables, self.file_list_container, progress_callback)
        logging.info(f"Finished extracting file: {file}")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ex = PDFProcessor()
    ex.show()
    sys.exit(app.exec_())
