import sys
import os
import re
from dataclasses import dataclass
from typing import Optional, List, Dict

import camelot
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets


#############################################################################
#                           Parsing / Logic Functions                        #
#############################################################################

def parse_marks_and_description(text: str):
    match_1z = re.search(r"(?i)(1Z[A-Za-z0-9]+)(?![A-Za-z0-9])", text)
    if match_1z:
        container_number = match_1z.group(0).strip()
        container_number = re.sub(r"(?i)of$", "", container_number).strip()
    else:
        match_container = re.search(r"(?i)Number and kind\s*(\S+)", text)
        container_number = match_container.group(1).strip() if match_container else ""

    match_desc = re.search(r"(?i)Description:\s*(.+)", text)
    description = match_desc.group(1).strip() if match_desc else ""
    return container_number, description


def parse_commodity_and_grossmass(text: str):
    commodity_code = ""
    gross_mass = ""

    pattern_commodity = re.compile(r"33 Commodity \(HS\) Code(\d+)", re.IGNORECASE)
    match_com = pattern_commodity.search(text)
    if match_com:
        raw = match_com.group(1)
        commodity_code = raw[:-2] if len(raw) >= 2 else raw

    pattern_gross = re.compile(r"35 Gross Mass \(Kg\)[A-Za-z]*(\d+\.\d+)", re.IGNORECASE)
    match_gross = pattern_gross.search(text)
    if match_gross:
        gross_mass = match_gross.group(1)

    return commodity_code, gross_mass


def parse_all_numbers(text: str):
    text = text.replace("\n", " ")
    nums = re.findall(r"[\d,\.]+", text)
    cleaned = []
    for val in nums:
        # ignore weird stray "42" you previously filtered
        if val.replace(",", "").replace(".", "") == "42":
            continue
        cleaned.append(val)
    return cleaned


def parse_item_price(text: str):
    found = parse_all_numbers(text)
    return found[-1] if found else ""


def extract_filtered_data_with_following_rows(pdf_path: str, rows_after: int = 4) -> Optional[pd.DataFrame]:
    """
    Extracts relevant blocks from PDF tables and returns a DataFrame.
    """
    try:
        tables = camelot.read_pdf(
            pdf_path,
            pages="all",
            flavor="lattice",          # consider switching to 'stream' if lattice fails for some PDFs
            strip_text="\n",
            line_scale=40
        )

        patterns = ["31 Packages", "Description of Goods"]
        all_data_rows: List[Dict[str, str]] = []

        for table in tables:
            df = table.df
            df.columns = [f"col_{i}" for i in range(len(df.columns))]

            match_mask = df.apply(
                lambda row: row.astype(str).str.contains("|".join(patterns), na=False, case=False).any(),
                axis=1
            )
            match_indices = match_mask[match_mask].index

            for match_index in match_indices:
                start_index = match_index
                end_index = min(match_index + rows_after + 1, len(df))
                matched_block = df.iloc[start_index:end_index]

                # Parse container number & description from col_1
                col1_lines = matched_block.get("col_1", pd.Series(dtype=str)).dropna().astype(str).tolist()
                filtered_lines = [ln for ln in col1_lines if ln.strip().lower() != "marks"]
                col1_text = " ".join(filtered_lines).strip()
                col1_text = re.sub(r"(?i)(1Z[A-Za-z0-9]+)(marks)", r"\1 Marks", col1_text)
                container_number, description = parse_marks_and_description(col1_text)

                # Parse commodity code & gross mass from col_12
                col12_text = " ".join(matched_block.get("col_12", pd.Series(dtype=str)).dropna().astype(str)).strip()
                commodity_code, gross_mass = parse_commodity_and_grossmass(col12_text)

                # Parse item price from col_16
                col16_text = " ".join(matched_block.get("col_16", pd.Series(dtype=str)).dropna().astype(str)).strip()
                item_price = parse_item_price(col16_text)

                if not item_price:
                    combined_text = f"{col12_text} {col16_text}"
                    combined_nums = parse_all_numbers(combined_text)
                    if combined_nums:
                        if gross_mass in combined_nums:
                            combined_nums.remove(gross_mass)
                        if combined_nums:
                            item_price = combined_nums[-1]

                all_data_rows.append({
                    "Marks & Nosof Packages": container_number,
                    "Description": description,
                    "Commodity_Code": commodity_code,
                    "Gross_Mass": gross_mass,
                    "Item_Price": item_price
                })

        if not all_data_rows:
            return None

        return pd.DataFrame(all_data_rows)

    except Exception as e:
        raise RuntimeError(f"Failed to process the PDF: {e}")


#############################################################################
#                   PyQt Worker Thread (background processing)               #
#############################################################################

class ProcessPDFThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(object, str)  # (df_or_none, error_message)

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path

    def run(self):
        try:
            df = extract_filtered_data_with_following_rows(self.pdf_path)
            if df is None or df.empty:
                self.finished.emit(pd.DataFrame(), "No matching data found.")
            else:
                self.finished.emit(df, "")
        except Exception as e:
            self.finished.emit(pd.DataFrame(), str(e))


#############################################################################
#                          Table Model (clean preview)                       #
#############################################################################

class DataFrameTableModel(QtCore.QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()

    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            return "" if pd.isna(value) else str(value)

        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def set_df(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df if df is not None else pd.DataFrame()
        self.endResetModel()


#############################################################################
#                       Modern UI + Dialog Integration                       #
#############################################################################

class PDFToExcelDialog(QtWidgets.QWidget):
    """
    This is a QWidget so it can be used inside your QStackedWidget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pdf_path: Optional[str] = None
        self.dataframe: Optional[pd.DataFrame] = None
        self.thread: Optional[ProcessPDFThread] = None

        self._build_ui()
        self._wire_events()
        self._set_initial_state()

    def _build_ui(self):
        self.setObjectName("ExtractInvoicePage")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # Header bar
        appbar = QtWidgets.QFrame(self)
        appbar.setObjectName("AppBar")
        appbar_layout = QtWidgets.QHBoxLayout(appbar)
        appbar_layout.setContentsMargins(18, 14, 18, 14)
        appbar_layout.setSpacing(12)

        self.btn_back = QtWidgets.QPushButton("← Back", appbar)
        self.btn_back.setObjectName("Secondary")
        self.btn_back.setMinimumHeight(40)

        title_box = QtWidgets.QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QtWidgets.QLabel("Extract Invoice Data", appbar)
        lbl_title.setObjectName("Title")

        lbl_sub = QtWidgets.QLabel("Select a PDF, extract table fields, preview, then export to Excel.", appbar)
        lbl_sub.setObjectName("Subtitle")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)

        appbar_layout.addWidget(self.btn_back, 0)
        appbar_layout.addLayout(title_box, 1)

        root.addWidget(appbar)

        # Card: controls
        card_controls = QtWidgets.QFrame(self)
        card_controls.setObjectName("Card")
        ctl = QtWidgets.QVBoxLayout(card_controls)
        ctl.setContentsMargins(18, 18, 18, 18)
        ctl.setSpacing(12)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)

        self.btn_select = QtWidgets.QPushButton("Select PDF & Extract", self)
        self.btn_select.setMinimumHeight(44)

        self.btn_dummy = QtWidgets.QPushButton("Load Dummy Data", self)
        self.btn_dummy.setObjectName("Secondary")
        self.btn_dummy.setMinimumHeight(44)

        self.btn_download = QtWidgets.QPushButton("Download Result (.xlsx)", self)
        self.btn_download.setObjectName("Secondary")
        self.btn_download.setMinimumHeight(44)

        row.addWidget(self.btn_select)
        row.addWidget(self.btn_dummy)
        row.addWidget(self.btn_download)

        self.lbl_file = QtWidgets.QLabel("", self)
        self.lbl_file.setStyleSheet("color: #A8A8A8;")
        self.lbl_file.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setVisible(False)          # start hidden
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.lbl_status = QtWidgets.QLabel("", self)
        self.lbl_status.setObjectName("Status")

        ctl.addLayout(row)
        ctl.addWidget(self.lbl_file)
        ctl.addWidget(self.progress)
        ctl.addWidget(self.lbl_status)

        root.addWidget(card_controls)

        # Card: preview
        card_preview = QtWidgets.QFrame(self)
        card_preview.setObjectName("Card")
        pv = QtWidgets.QVBoxLayout(card_preview)
        pv.setContentsMargins(18, 18, 18, 18)
        pv.setSpacing(12)

        preview_title = QtWidgets.QLabel("Preview", self)
        preview_title.setStyleSheet("font-size: 13pt; font-weight: 800; color: #FFFFFF;")

        self.table = QtWidgets.QTableView(self)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        self.model = DataFrameTableModel(pd.DataFrame())
        self.table.setModel(self.model)

        pv.addWidget(preview_title)
        pv.addWidget(self.table)

        root.addWidget(card_preview, 1)

    def _wire_events(self):
        self.btn_select.clicked.connect(self.on_select_pdf)
        self.btn_dummy.clicked.connect(self.load_dummy_data)
        self.btn_download.clicked.connect(self.on_download)
        self.btn_back.clicked.connect(self.on_back)

    def _set_initial_state(self):
        self.btn_download.setEnabled(False)
        self._set_status("Choose a PDF to extract data, or load dummy data to test UI.")
        self._resize_table()

    def _set_status(self, msg: str):
        self.lbl_status.setText(msg)

    def _set_file_label(self, path: Optional[str]):
        if not path:
            self.lbl_file.setText("")
            self.lbl_file.setToolTip("")
            return
        base = os.path.basename(path)
        self.lbl_file.setText(f"Selected file: {base}")
        self.lbl_file.setToolTip(path)

    def _resize_table(self):
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def _set_busy(self, busy: bool):
        self.btn_select.setEnabled(not busy)
        self.btn_dummy.setEnabled(not busy)
        self.btn_download.setEnabled((not busy) and self.dataframe is not None and not self.dataframe.empty)

        if busy:
            self.progress.setVisible(True)
            # Indeterminate mode: this is the correct "loading" behavior
            self.progress.setRange(0, 0)
        else:
            self.progress.setVisible(False)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    #############################################################################
    #                              Actions                                      #
    #############################################################################

    def on_select_pdf(self):
        pdf_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not pdf_file:
            return

        self.pdf_path = pdf_file
        self._set_file_label(pdf_file)

        self.dataframe = None
        self.model.set_df(pd.DataFrame())
        self._resize_table()

        self._set_status("Processing… please wait.")
        self._set_busy(True)

        self.thread = ProcessPDFThread(pdf_path=self.pdf_path)
        self.thread.finished.connect(self.on_process_finished)
        self.thread.start()

    def on_process_finished(self, df, error_message: str):
        self._set_busy(False)

        if error_message:
            self._set_status(f"Error: {error_message}")
            QtWidgets.QMessageBox.critical(self, "Error", error_message)
            return

        if df is None or df.empty:
            self._set_status("No matching data found.")
            self.btn_download.setEnabled(False)
            return

        self.dataframe = df
        self.model.set_df(df)
        self._resize_table()

        self._set_status(f"Done. Extracted {len(df)} row(s). You can download now.")
        self.btn_download.setEnabled(True)

    def on_download(self):
        if self.dataframe is None or self.dataframe.empty:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data to download.")
            return

        save_file, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        if not save_file:
            return

        if not save_file.lower().endswith(".xlsx"):
            save_file += ".xlsx"

        try:
            self.dataframe.to_excel(save_file, index=False)
            QtWidgets.QMessageBox.information(self, "Success", f"File saved to:\n{save_file}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Unable to save file:\n{e}")

    def on_back(self):
        # In your stacked app, app.py handles switching pages.
        # We just close/hide in case it's used standalone.
        self.close()

    #############################################################################
    #                            Dummy Data                                     #
    #############################################################################

    def load_dummy_data(self):
        """
        Loads dummy data so you can test UI without a PDF.
        """
        dummy = pd.DataFrame([
            {
                "Marks & Nosof Packages": "1Z999AA10123456784",
                "Description": "Spare parts - metal fittings (sample)",
                "Commodity_Code": "870899",
                "Gross_Mass": "1250.50",
                "Item_Price": "1499.99"
            },
            {
                "Marks & Nosof Packages": "CONT-ABCD-778899",
                "Description": "Printed labels / packaging materials",
                "Commodity_Code": "481910",
                "Gross_Mass": "420.00",
                "Item_Price": "300.00"
            },
            {
                "Marks & Nosof Packages": "1Z77BB99112233445",
                "Description": "Electronics accessories (sample)",
                "Commodity_Code": "854442",
                "Gross_Mass": "88.75",
                "Item_Price": "259.50"
            }
        ])

        self.pdf_path = None
        self._set_file_label(None)

        self.dataframe = dummy
        self.model.set_df(dummy)
        self._resize_table()

        self.btn_download.setEnabled(True)
        self._set_status("Dummy data loaded. Preview and download to test Excel export.")


#############################################################################
#                               Standalone Run                               #
#############################################################################

def main():
    app = QtWidgets.QApplication(sys.argv)
    dialog = PDFToExcelDialog()
    dialog.setWindowTitle("Extract Invoice Data")
    dialog.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()