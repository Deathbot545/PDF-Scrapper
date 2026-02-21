import sys
from PyQt5 import QtWidgets

from main import Ui_Dialog as Ui_MainWindow
from CompareCargoManifests import CompareCargoPage
from ExtractInvoiceData import PDFToExcelDialog


class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XtractPDF")
        self.setMinimumSize(900, 620)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_page = QtWidgets.QWidget()
        self.compare_page = CompareCargoPage()
        self.extract_page = PDFToExcelDialog()

        self.main_ui = Ui_MainWindow()
        self.main_ui.setupUi(self.main_page)

        self.stack.addWidget(self.main_page)     # 0
        self.stack.addWidget(self.compare_page)  # 1
        self.stack.addWidget(self.extract_page)  # 2

        # Navigation
        self.main_ui.Extractinvoicbutton.clicked.connect(lambda: self.switch_page(2))
        self.main_ui.pushButton_2.clicked.connect(lambda: self.switch_page(1))
        self.compare_page.btn_back.clicked.connect(lambda: self.switch_page(0))
        self.extract_page.btn_back.clicked.connect(lambda: self.switch_page(0))

        self.apply_dark_theme()

    def apply_dark_theme(self):
        qss = """
        * {
            font-family: "Segoe UI";
            font-size: 11pt;
        }

        QMainWindow, QWidget {
            background-color: #121212;
            color: #EAEAEA;
        }

        /* App bar */
        QWidget#AppBar {
            background-color: #161616;
            border: 1px solid #222222;
            border-radius: 14px;
        }

        QLabel#Title {
            font-size: 22pt;
            font-weight: 700;
            color: #FFFFFF;
        }

        QLabel#Subtitle {
            color: #A8A8A8;
            font-size: 10.5pt;
        }

        /* Primary buttons */
        QPushButton {
            background-color: #8B5CF6;
            color: #FFFFFF;
            border: none;
            border-radius: 12px;
            padding: 10px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #7C3AED;
        }
        QPushButton:pressed {
            background-color: #6D28D9;
        }
        QPushButton:disabled {
            background-color: #2A2A2A;
            color: #777777;
        }

        /* Secondary button */
        QPushButton#Secondary {
            background-color: #1E1E1E;
            border: 1px solid #2C2C2C;
            color: #EAEAEA;
        }
        QPushButton#Secondary:hover {
            background-color: #242424;
        }

        /* Cards */
        QFrame#Card {
            background-color: #161616;
            border: 1px solid #242424;
            border-radius: 16px;
        }

        /* ---- CLEARER TABLE THEME ---- */
        QTableView {
            background-color: #141414;
            border: 1px solid #242424;
            border-radius: 12px;
            gridline-color: #2E2E2E;
            color: #EDEDED;
            padding: 6px;
            alternate-background-color: #1B1B1B;
            selection-background-color: #2B1D4A;
            selection-color: #FFFFFF;
        }

        QTableView::item {
            padding: 8px 10px;
            border-bottom: 1px solid #222222;
        }

        QTableView::item:selected {
            background-color: #2B1D4A;
            color: #FFFFFF;
        }

        QHeaderView::section {
            background-color: #1A1A1A;
            color: #D6D6D6;
            padding: 10px;
            border: none;
            border-bottom: 1px solid #2C2C2C;
            font-weight: 800;
        }

        QLabel#Status {
            color: #BDBDBD;
            font-size: 10.5pt;
        }
        """
        self.setStyleSheet(qss)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())