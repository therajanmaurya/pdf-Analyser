from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QProgressBar, QDesktopWidget, QApplication,
    QScrollArea, QSizePolicy, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import logging
import os
import subprocess
from pdf_processing import create_filtered_pdf
from PyPDF2 import PdfReader  # Correct import for PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PDFProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.filtered_files = []  # Store paths to filtered PDFs
        self.progress_bars = []
        self.initUI()
        self.load_radio_button_state()  # Load the radio button state

    def initUI(self):
        # Set the window title and icon
        self.setWindowTitle("PDF Processor")

        # Set the window to 75% of the screen size
        screen_geometry = QDesktopWidget().availableGeometry()
        width = int(screen_geometry.width() * 0.75)
        height = int(screen_geometry.height() * 0.75)
        self.setGeometry(0, 0, width, height)
        self.move((screen_geometry.width() - width) // 2, (screen_geometry.height() - height) // 2)

        # Main layout
        self.layout = QVBoxLayout()

        # Header layout
        header_layout = QHBoxLayout()

        # Radio buttons for "Plans" and "Specifications"
        self.radio_group = QButtonGroup(self)
        self.plans_radio = QRadioButton("Plans")
        self.specifications_radio = QRadioButton("Specifications")
        self.radio_group.addButton(self.plans_radio)
        self.radio_group.addButton(self.specifications_radio)
        self.plans_radio.setChecked(True)  # Default to "Plans"

        # Connect radio buttons to save state method
        self.plans_radio.toggled.connect(self.save_radio_button_state)
        self.specifications_radio.toggled.connect(self.save_radio_button_state)

        # Layout for radio buttons
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.plans_radio)
        radio_layout.addWidget(self.specifications_radio)
        radio_layout.addStretch()

        # Add radio layout to the header layout
        header_layout.addLayout(radio_layout)

        # Set an image when there are no files
        self.icon_image = QLabel()
        self.icon_image.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap('brucker_logo.png')  # Set the path to your image file
        self.icon_image.setPixmap(pixmap)
        header_layout.addWidget(self.icon_image)
        header_layout.addStretch()

        self.layout.addLayout(header_layout)

        # Scroll area for file list and progress bars
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.file_list_container = QVBoxLayout(self.scroll_area_widget)
        self.file_list_container.setAlignment(Qt.AlignTop)  # Align the content to the top
        self.scroll_area_widget.setLayout(self.file_list_container)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.layout.addWidget(self.scroll_area)

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
            logging.info(f"Selected files: {self.selected_files}")
        self.extract_button.setEnabled(bool(self.selected_files))

    def reset_selection(self):
        self.selected_files = []
        self.filtered_files = []  # Reset filtered files
        self.progress_bars = []
        self.update_file_list_container()
        self.extract_button.setEnabled(False)
        logging.info("Selection reset")

    def extract_all_pdfs(self):
        self.thread = QThread()
        self.worker = ExtractWorker(self.selected_files, self.filtered_files, self.file_list_container,
                                    self.get_current_filter_type())
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.enable_open_button.connect(self.enable_open_button)  # Connect the signal to the slot
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()
        logging.info("Started extracting all PDFs")

    def get_current_filter_type(self):
        return "Plans" if self.plans_radio.isChecked() else "Specifications"

    def update_file_list_container(self):
        for i in reversed(range(self.file_list_container.count())):
            widget_to_remove = self.file_list_container.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        self.progress_bars = []
        for index, file in enumerate(self.selected_files):
            file_layout = QVBoxLayout()
            file_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding
            file_layout.setSpacing(0)  # Remove spacing

            # Create alias for the file
            alias = os.path.basename(file)

            file_label = QLabel(alias)
            file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_label.setToolTip(file)  # Show full path on hover
            file_layout.addWidget(file_label)

            # Layout for progress bar and buttons
            progress_button_layout = QHBoxLayout()
            progress_button_layout.setSpacing(0)  # Remove spacing between widgets
            progress_button_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding

            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            progress_button_layout.addWidget(progress_bar)
            self.progress_bars.append(progress_bar)

            extract_button = QPushButton('Extract')
            extract_button.clicked.connect(lambda checked, f=file, i=index: self.extract_pdf(f, i))
            progress_button_layout.addWidget(extract_button)

            open_button = QPushButton('Open')
            open_button.setEnabled(False)
            open_button.clicked.connect(lambda checked, i=index: self.open_pdf(i))
            progress_button_layout.addWidget(open_button)

            file_layout.addLayout(progress_button_layout)

            container_widget = QWidget()
            container_widget.setLayout(file_layout)
            container_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.file_list_container.addWidget(container_widget)

    def extract_pdf(self, file, index):
        self.thread = QThread()
        self.worker = ExtractWorker([file], self.filtered_files, self.file_list_container,
                                    self.get_current_filter_type(), index)
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.enable_open_button.connect(self.enable_open_button)  # Connect the signal to the slot
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()
        logging.info(f"Started extracting PDF: {file}")

    def update_progress(self, index, progress):
        progress_bar = self.progress_bars[index]
        progress_bar.setValue(progress)
        logging.info(f"Progress for file {index}: {progress}%")

    def enable_open_button(self, index):
        # This function enables the 'Open' button after extraction
        container_widget = self.file_list_container.itemAt(index).widget()
        if container_widget:
            progress_button_layout = container_widget.layout().itemAt(1)
            if progress_button_layout:
                open_button = progress_button_layout.itemAt(
                    2).widget()  # Assuming 'Open' is the third widget in the layout
                if open_button:
                    open_button.setEnabled(True)

    def open_pdf(self, index):
        try:
            filtered_file = self.filtered_files[index]  # Get the filtered PDF path
            if os.name == 'posix':
                subprocess.call(['open', filtered_file])
            elif os.name == 'nt':
                os.startfile(filtered_file)
            elif os.name == 'mac':
                subprocess.call(['open', filtered_file])
        except Exception as e:
            logging.error(f"Error opening PDF: {e}")

    def save_radio_button_state(self):
        state = "Plans" if self.plans_radio.isChecked() else "Specifications"
        with open("radio_button_state.txt", "w") as file:
            file.write(state)
        logging.info(f"Radio button state saved: {state}")

    def load_radio_button_state(self):
        if os.path.exists("radio_button_state.txt"):
            with open("radio_button_state.txt", "r") as file:
                state = file.read().strip()
            if state == "Plans":
                self.plans_radio.setChecked(True)
            else:
                self.specifications_radio.setChecked(True)
            logging.info(f"Radio button state loaded: {state}")


class ExtractWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    enable_open_button = pyqtSignal(int)  # Define a new signal

    def __init__(self, files, filtered_files, file_list_container, filter_type, index=None):
        super().__init__()
        self.files = files
        self.filtered_files = filtered_files  # Add filtered files list
        self.file_list_container = file_list_container
        self.index = index
        self.filter_type = filter_type

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

        filtered_pdf = create_filtered_pdf(file, self.filter_type, progress_callback)
        self.filtered_files.insert(index, filtered_pdf)  # Store the filtered PDF path

        # Emit the signal to enable the Open button once the file is filtered
        self.enable_open_button.emit(index)

        logging.info(f"Finished extracting file: {file}")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ex = PDFProcessor()
    ex.show()
    sys.exit(app.exec_())
