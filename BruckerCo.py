import sys
from PyQt5.QtWidgets import QApplication
from pdf_processor import PDFProcessor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFProcessor()
    ex.show()
    sys.exit(app.exec_())
