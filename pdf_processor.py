from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QHBoxLayout, QScrollArea, QSizePolicy, QRadioButton,
    QButtonGroup, QMessageBox, QFrame, QDesktopWidget, QApplication, QProgressBar
)
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import logging
import os
import subprocess
import time
from pdf_processing import create_filtered_pdf, create_pdf_between_indices
from PyPDF2 import PdfReader
import resources_rc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super(CircularProgress, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowModality(Qt.ApplicationModal)  # Ensure the overlay blocks interactions

        # Set the layout and label
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 128);")

        # Center the circular progress indicator
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Load the spinning GIF (Replace with your own spinner.gif)
        movie = QMovie(":/spinner.gif")
        self.label.setMovie(movie)
        movie.start()

        self.hide()

    def resizeEvent(self, event):
        # Ensure the progress indicator stays centered
        self.label.move((self.width() - self.label.width()) // 2,
                        (self.height() - self.label.height()) // 2)


class PDFProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.filtered_files = []  # Store paths to filtered PDFs
        self.progress_bars = []
        self.progress_labels = []  # Store progress labels (percentage and timer)
        self.start_times = []  # Store start times for each file extraction
        self.thread = None
        self.worker = None
        self.is_resetting = False  # Flag to indicate if a reset is in progress
        self.circular_progress = CircularProgress(self)  # Initialize the CircularProgress overlay
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

        # Radio buttons for "PLANS" and "SPECIFICATIONS"
        self.radio_group = QButtonGroup(self)
        self.plans_radio = QRadioButton("PLANS")
        self.specifications_radio = QRadioButton("SPECIFICATIONS")
        self.radio_group.addButton(self.plans_radio)
        self.radio_group.addButton(self.specifications_radio)
        self.plans_radio.setChecked(True)  # Default to "PLANS"

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

        # # Set an image when there are no files
        # self.icon_image = QLabel()
        # self.icon_image.setAlignment(Qt.AlignCenter)
        # pixmap = QPixmap(':/ocr.png')  # Set the path to your image file
        # self.icon_image.setPixmap(pixmap)
        # header_layout.addWidget(self.icon_image)
        # header_layout.addStretch()
        #
        # self.layout.addLayout(header_layout)

        # Add OCR text below the icon image
        ocr_label = QLabel("OCR")
        ocr_label.setAlignment(Qt.AlignCenter)
        ocr_label.setStyleSheet("font-weight: bold; font-size: 24px;")
        self.layout.addWidget(ocr_label)
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
        self.reset_button = QPushButton('Reset/Cancel', self)
        self.reset_button.clicked.connect(self.reset_selection)
        self.buttons_layout.addWidget(self.reset_button)

        # Extract button
        self.extract_button = QPushButton('Extract', self)
        self.extract_button.clicked.connect(self.extract_all_pdfs)
        self.extract_button.setEnabled(False)
        self.buttons_layout.addWidget(self.extract_button)

        # Adding the buttons layout to the main layout
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

    def toggle_buttons(self, enable):
        self.select_button.setEnabled(enable)

        # Only enable the "Extract" button if there are unprocessed PDFs
        if enable and any(pb.value() < 100 for pb in self.progress_bars):
            self.extract_button.setEnabled(True)
        else:
            self.extract_button.setEnabled(False)

    def select_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)",
                                                options=options)
        if files:
            # Filter out files that are already in the list
            new_files = [file for file in files if file not in self.selected_files]
            if new_files:
                self.selected_files.extend(new_files)
                self.update_file_list_container(new_files)
                logging.info(f"Selected files: {new_files}")
            else:
                logging.info("No new files selected.")
        self.toggle_buttons(True)

    def reset_selection(self):
        if self.thread and self.thread.isRunning():
            # If a thread is running, cancel the worker and reset states
            self.is_resetting = True
            self.show_circular_progress()  # Show the circular progress overlay
            if self.worker:
                self.worker.cancel()
            self.thread.finished.connect(self.reset_states)
        else:
            # No thread is running, so clear the list and reset states
            self.complete_reset()

    def complete_reset(self):
        self.thread = None
        self.worker = None
        self.is_resetting = False

        self.toggle_buttons(False)  # Disable buttons
        self.selected_files = []
        self.filtered_files = []  # Reset filtered files
        self.progress_bars = []
        self.progress_labels = []  # Reset progress labels
        self.start_times = []  # Reset start times

        # Clear all widgets in the file list container
        while self.file_list_container.count():
            child = self.file_list_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.toggle_buttons(True)  # Re-enable buttons after reset
        self.hide_circular_progress()  # Hide the overlay when done
        logging.info("Selection reset")

    def reset_states(self):
        self.thread = None
        self.worker = None
        self.is_resetting = False

        # Reset progress bars and related states
        for pb in self.progress_bars:
            pb.setValue(0)
        for index, _ in enumerate(self.start_times):
            self.start_times[index] = None
            progress_percentage_label, progress_timer_label = self.progress_labels[index]
            progress_percentage_label.setText("0%")
            progress_timer_label.setText("0s")

        self.toggle_buttons(True)  # Re-enable buttons
        self.hide_circular_progress()  # Hide the overlay when done
        logging.info("States reset, ready for new extraction.")

    def extract_all_pdfs(self):
        # Check if the filter type is "SPECIFICATIONS"
        if self.get_current_filter_type() == "SPECIFICATIONS":
            # Check if any file name contains "spec" (case-insensitive)
            contains_spec = any("spec" in os.path.basename(file).lower() for file in self.selected_files)

            if not contains_spec:
                # Show a warning dialog
                reply = QMessageBox.question(self, 'Warning',
                                             "Are you sure, you selected Specifications files?",
                                             QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    logging.info("User cancelled the extraction process for SPECIFICATIONS.")
                    return  # Do not start the extraction process

        unprocessed_indices = [i for i, pb in enumerate(self.progress_bars) if pb.value() < 100]

        if not unprocessed_indices:
            logging.info("All files are already processed.")
            self.toggle_buttons(True)
            return

        self.toggle_buttons(False)  # Disable buttons

        # Initialize start_times with None for each file
        self.start_times = [None] * len(self.selected_files)

        self.thread = QThread()
        self.worker = ExtractWorker(
            self.selected_files, self.filtered_files, self.file_list_container,
            self.get_current_filter_type(), unprocessed_indices
        )
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.enable_open_button.connect(self.enable_open_button)  # Connect the signal to the slot

        # Re-enable buttons after extraction is complete
        self.worker.finished.connect(lambda: self.toggle_buttons(True))
        # Do not call complete_reset here, as we want to keep the list
        self.thread.finished.connect(lambda: logging.info("Processing completed"))

        self.thread.started.connect(self.worker.run)
        self.thread.start()
        logging.info("Started extracting unprocessed PDFs")

    def get_current_filter_type(self):
        return "PLANS" if self.plans_radio.isChecked() else "SPECIFICATIONS"

    def update_file_list_container(self, new_files=None):
        if new_files is None:
            new_files = self.selected_files

        for file in new_files:
            index = self.selected_files.index(file)
            file_layout = QVBoxLayout()
            file_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding
            file_layout.setSpacing(5)  # Add slight spacing for clarity

            # Create alias for the file
            alias = os.path.basename(file)

            file_label = QLabel(alias)
            file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_label.setToolTip(file)  # Show full path on hover
            file_layout.addWidget(file_label)

            # Layout for progress bar and open button (Horizontal layout)
            progress_button_layout = QHBoxLayout()
            progress_button_layout.setSpacing(5)  # Small spacing between widgets
            progress_button_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding

            progress_bar = QProgressBar()
            if len(self.progress_bars) > index:
                # Use existing progress if it exists
                progress_bar.setValue(self.progress_bars[index].value())
            else:
                progress_bar.setValue(0)
                self.progress_bars.append(progress_bar)

            progress_button_layout.addWidget(progress_bar)

            open_button = QPushButton('Open')
            open_button.setEnabled(False)
            open_button.clicked.connect(lambda checked, i=index: self.open_pdf(i))
            progress_button_layout.addWidget(open_button)

            file_layout.addLayout(progress_button_layout)

            # Layout for progress percentage and timer (New horizontal layout)
            progress_info_layout = QHBoxLayout()
            progress_info_layout.setSpacing(5)  # Spacing between items

            progress_percentage_label = QLabel(f"{progress_bar.value()}%")  # Set initial percentage label
            progress_timer_label = QLabel("0s")  # Initial timer label
            separator_label = QLabel("|")  # Separator between percentage and time

            progress_info_layout.addWidget(progress_percentage_label)
            progress_info_layout.addWidget(separator_label)
            progress_info_layout.addWidget(progress_timer_label)

            # Align labels to the left
            progress_info_layout.addStretch()

            if len(self.progress_labels) > index:
                self.progress_labels[index] = (progress_percentage_label, progress_timer_label)
            else:
                self.progress_labels.append((progress_percentage_label, progress_timer_label))

            file_layout.addLayout(progress_info_layout)

            # Add a divider line between list items with no left or right padding
            if index < len(self.selected_files) - 1:
                divider = QFrame()
                divider.setFrameShape(QFrame.HLine)
                divider.setFrameShadow(QFrame.Sunken)
                divider.setLineWidth(1)  # Set the line width to make it visible
                divider.setStyleSheet("background-color: rgba(0, 0, 0, 0.2);")  # Set the divider color to 20% black
                divider.setFixedHeight(1)  # Ensure the divider is thin

                # Ensure the divider spans the entire width of the parent container
                divider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

                # Remove all margins from the layout containing the divider
                divider_layout = QVBoxLayout()
                divider_layout.setContentsMargins(0, 10, 0, 10)  # Only top and bottom padding
                divider_layout.setSpacing(0)  # No extra spacing
                divider_layout.addWidget(divider)

                file_layout.addLayout(divider_layout)

            container_widget = QWidget()
            container_widget.setLayout(file_layout)
            container_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.file_list_container.addWidget(container_widget)

    def update_progress(self, index, progress):
        if self.is_resetting:
            return

        if index >= len(self.progress_bars):
            return  # Prevent IndexError if reset occurs during processing

        progress_bar = self.progress_bars[index]
        progress_bar.setValue(progress)

        # Initialize start time when processing begins
        if self.start_times[index] is None:
            self.start_times[index] = time.time()

        elapsed_time = int(time.time() - self.start_times[index])  # Calculate elapsed time

        # Format elapsed time
        if elapsed_time < 60:
            formatted_time = f"{elapsed_time}s"
        else:
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            formatted_time = f"{minutes}m {seconds}s"

        progress_percentage_label, progress_timer_label = self.progress_labels[index]
        progress_percentage_label.setText(f"{progress}%")  # Update the percentage label
        progress_timer_label.setText(formatted_time)  # Update the timer label

        logging.info(f"Progress for file {index}: {progress}%")

        # Check if all files have reached 100% progress
        all_done = all(pb.value() == 100 for pb in self.progress_bars)
        if all_done:
            self.extract_button.setEnabled(False)

    def enable_open_button(self, index):
        if index >= len(self.filtered_files):
            return  # Prevent IndexError if reset occurs during processing

        # This function enables the 'Open' button after extraction
        container_widget = self.file_list_container.itemAt(index).widget()
        if container_widget:
            progress_button_layout = container_widget.layout().itemAt(1)
            if progress_button_layout:
                open_button = progress_button_layout.itemAt(
                    1).widget()  # Assuming 'Open' is the second widget in the layout
                if open_button:
                    open_button.setEnabled(True)

    def open_pdf(self, index):
        if index >= len(self.filtered_files):
            return  # Prevent IndexError if reset occurs during processing

        try:
            filtered_file = self.filtered_files[index]  # Get the filtered PDF path
            with open(filtered_file, 'rb') as f:
                pdf_reader = PdfReader(f)
                if len(pdf_reader.pages) == 0:
                    QMessageBox.information(self, "Found Nothing", "The filtered PDF is empty.")
                    return
            if os.name == 'posix':
                subprocess.call(['open', filtered_file])
            elif os.name == 'nt':
                os.startfile(filtered_file)
            elif os.name == 'mac':
                subprocess.call(['open', filtered_file])
        except Exception as e:
            logging.error(f"Error opening PDF: {e}")
            QMessageBox.critical(self, "Error", f"Error opening PDF: {e}")

    def save_radio_button_state(self):
        state = "PLANS" if self.plans_radio.isChecked() else "SPECIFICATIONS"
        with open("radio_button_state.txt", "w") as file:
            file.write(state)
        logging.info(f"Radio button state saved: {state}")

    def load_radio_button_state(self):
        if os.path.exists("radio_button_state.txt"):
            with open("radio_button_state.txt", "r") as file:
                state = file.read().strip()
            if state == "PLANS":
                self.plans_radio.setChecked(True)
            else:
                self.specifications_radio.setChecked(True)
            logging.info(f"Radio button state loaded: {state}")

    def show_circular_progress(self):
        self.circular_progress.resize(self.size())  # Make sure the overlay covers the entire window
        self.circular_progress.show()

    def hide_circular_progress(self):
        self.circular_progress.hide()


class ExtractWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    enable_open_button = pyqtSignal(int)  # Define a new signal

    def __init__(self, files, filtered_files, file_list_container, filter_type, unprocessed_indices):
        super().__init__()
        self.files = files
        self.filtered_files = filtered_files  # Add filtered files list
        self.file_list_container = file_list_container
        self.filter_type = filter_type
        self.unprocessed_indices = unprocessed_indices  # Indices of files to process
        self._is_canceled = False

    def run(self):
        for index in self.unprocessed_indices:
            if self._is_canceled:
                break
            self.extract_single_file(self.files[index], index)
        self.finished.emit()

    def extract_single_file(self, file, index):
        def progress_callback(progress):
            if self._is_canceled:
                raise Exception("Extraction cancelled by user.")
            self.progress.emit(index, progress)

        if self._is_canceled:
            return

        filtered_pdf = None  # Initialize to None

        try:
            if self.filter_type == "PLANS":
                filtered_pdf = create_filtered_pdf(file, self.filter_type, progress_callback)
            elif self.filter_type == "SPECIFICATIONS":
                filtered_pdf = create_pdf_between_indices(file, progress_callback)

            if filtered_pdf:  # Check if a valid PDF was created
                self.filtered_files.insert(index, filtered_pdf)  # Store the filtered PDF path
                # Emit the signal to enable the Open button once the file is filtered
                self.enable_open_button.emit(index)
                logging.info(f"Finished extracting file: {file}")
            else:
                logging.error(f"Failed to create filtered PDF for file: {file}")

        except Exception as e:
            if self._is_canceled:
                logging.info(f"Extraction canceled for file: {file}")
            else:
                logging.error(f"Error during extraction: {e}")

    def cancel(self):
        logging.info("Cancelling extraction")
        self._is_canceled = True


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ex = PDFProcessor()
    ex.show()
    sys.exit(app.exec_())
