import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pdfplumber
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets


@dataclass
class SelectedFiles:
    parent_1: Optional[str] = None
    parent_2: Optional[str] = None
    child: Optional[str] = None

    def all_selected(self) -> bool:
        return bool(self.parent_1 and self.parent_2 and self.child)


def clean_cell(value):
    if isinstance(value, str):
        return value.replace("\\n", " ").replace("\n", " ").strip()
    return value


def extract_tables_from_page(page) -> List[pd.DataFrame]:
    tables = page.extract_tables() or []
    dfs: List[pd.DataFrame] = []

    for tbl in tables:
        if not tbl or len(tbl) < 2:
            continue
        header = [str(h).strip() if h is not None else "" for h in tbl[0]]
        rows = tbl[1:]
        dfs.append(pd.DataFrame(rows, columns=header))

    return dfs


def extract_all_tables(pdf_path: str) -> pd.DataFrame:
    all_dfs: List[pd.DataFrame] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_dfs.extend(extract_tables_from_page(page))

    if not all_dfs:
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    df = df.apply(lambda col: col.map(clean_cell))
    return df


def rename_columns_parent(df: pd.DataFrame) -> pd.DataFrame:
    rename: Dict[str, str] = {}

    if "HAWB\nNumber" in df.columns:
        rename["HAWB\nNumber"] = "HAWB"

    if "Origin" not in df.columns:
        origin_candidates = [c for c in df.columns if "origin" in str(c).lower()]
        if len(origin_candidates) == 1:
            rename[origin_candidates[0]] = "Origin"

    return df.rename(columns=rename)


def rename_columns_child(df: pd.DataFrame) -> pd.DataFrame:
    rename: Dict[str, str] = {}

    if "HAWB\nShipment" in df.columns:
        rename["HAWB\nShipment"] = "HAWB"

    if "Secondary Tracking Numbers" in df.columns:
        rename["Secondary Tracking Numbers"] = "secondary"

    return df.rename(columns=rename)


def ensure_required_columns(df_parent: pd.DataFrame, df_child: pd.DataFrame) -> Tuple[bool, str]:
    if "HAWB" not in df_parent.columns:
        return False, "No 'HAWB' column found in Parent manifests."
    if not df_child.empty and "HAWB" not in df_child.columns:
        return False, "No 'HAWB' column found in Child manifest."
    return True, ""


def merge_parent_child(df_parent: pd.DataFrame, df_child: pd.DataFrame) -> pd.DataFrame:
    if df_child.empty:
        df_parent = df_parent.copy()
        if "secondary" not in df_parent.columns:
            df_parent["secondary"] = ""
        return df_parent

    df_merged = pd.merge(df_parent, df_child, on="HAWB", how="left", suffixes=("_parent", "_child"))
    if "secondary" not in df_merged.columns:
        df_merged["secondary"] = ""
    return df_merged


def expand_secondary_to_master_baby(df: pd.DataFrame) -> pd.DataFrame:
    final_rows: List[dict] = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        sec_str = row_dict.get("secondary", "") or ""
        if pd.isna(sec_str):
            sec_str = ""

        secondary_list = [s.strip() for s in str(sec_str).split(",") if s.strip()]

        master = row_dict.copy()
        master["Type"] = "Master"
        final_rows.append(master)

        for sec in secondary_list:
            baby = row_dict.copy()
            baby["Type"] = "Baby"
            baby["HAWB"] = sec
            final_rows.append(baby)

    return pd.DataFrame(final_rows)


def select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    parent_columns_order = [
        "Origin",
        "#",
        "HAWB",
        "Pcs",
        "Weight",
        "Shipper Details",
        "Dest",
        "Bill\nTerm",
        "Consignee Details",
        "Description\nof Goods",
        "Total\nValue",
        "Total\nValue(LKR)",
    ]
    final_cols = parent_columns_order + ["Type"]
    existing = [c for c in final_cols if c in df.columns]
    return df[existing].copy()


class CompareCargoPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = SelectedFiles()
        self.df_final: Optional[pd.DataFrame] = None

        self.setupUi(self)
        self._wire_events()
        self._set_initial_state()

    def _set_initial_state(self):
        self.btn_run.setEnabled(False)
        self.btn_download.setEnabled(False)
        self._set_status("Select 2 Parent PDFs + 1 Child PDF to continue.")

    def _wire_events(self):
        self.btn_parent1.clicked.connect(lambda: self._select_pdf("parent_1"))
        self.btn_parent2.clicked.connect(lambda: self._select_pdf("parent_2"))
        self.btn_child.clicked.connect(lambda: self._select_pdf("child"))
        self.btn_run.clicked.connect(self.run_merge)
        self.btn_download.clicked.connect(self.download_result)
        self.btn_back.clicked.connect(self.on_back)

    def setupUi(self, parent):
        parent.setObjectName("CompareCargo")
        parent.setMinimumSize(900, 620)

        root = QtWidgets.QVBoxLayout(parent)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        appbar = QtWidgets.QFrame(parent)
        appbar.setObjectName("AppBar")
        appbar_layout = QtWidgets.QHBoxLayout(appbar)
        appbar_layout.setContentsMargins(18, 14, 18, 14)
        appbar_layout.setSpacing(12)

        self.btn_back = QtWidgets.QPushButton("← Back", appbar)
        self.btn_back.setObjectName("Secondary")
        self.btn_back.setMinimumHeight(40)

        title_box = QtWidgets.QVBoxLayout()
        title_box.setSpacing(2)

        t = QtWidgets.QLabel("Compare Cargo Manifests", appbar)
        t.setObjectName("Title")

        s = QtWidgets.QLabel("Select PDFs, run processing, then export Excel.", appbar)
        s.setObjectName("Subtitle")

        title_box.addWidget(t)
        title_box.addWidget(s)

        appbar_layout.addWidget(self.btn_back, 0)
        appbar_layout.addLayout(title_box, 1)

        root.addWidget(appbar)

        card_files = QtWidgets.QFrame(parent)
        card_files.setObjectName("Card")
        files_layout = QtWidgets.QVBoxLayout(card_files)
        files_layout.setContentsMargins(18, 18, 18, 18)
        files_layout.setSpacing(12)

        self._make_row(files_layout, "Parent PDF 1", "btn_parent1", "lbl_p1")
        self._make_row(files_layout, "Parent PDF 2", "btn_parent2", "lbl_p2")
        self._make_row(files_layout, "Child Manifest", "btn_child", "lbl_child")

        root.addWidget(card_files)

        card_table = QtWidgets.QFrame(parent)
        card_table.setObjectName("Card")
        table_layout = QtWidgets.QVBoxLayout(card_table)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)

        self.tableView = QtWidgets.QTableView(card_table)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # UX: cleaner look
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setShowGrid(False)

        self.lbl_status = QtWidgets.QLabel("", card_table)
        self.lbl_status.setObjectName("Status")

        table_layout.addWidget(self.tableView)
        table_layout.addWidget(self.lbl_status)

        root.addWidget(card_table, 1)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(12)

        self.btn_download = QtWidgets.QPushButton("Download Excel", parent)
        self.btn_download.setMinimumHeight(44)
        self.btn_download.setObjectName("Secondary")

        self.btn_run = QtWidgets.QPushButton("Run", parent)
        self.btn_run.setMinimumHeight(44)

        actions.addStretch(1)
        actions.addWidget(self.btn_download)
        actions.addWidget(self.btn_run)

        root.addLayout(actions)

    def _make_row(self, parent_layout, label_text: str, btn_attr: str, lbl_attr: str):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)

        lbl = QtWidgets.QLabel(label_text)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet("color: #CFCFCF; font-weight: 600;")

        btn = QtWidgets.QPushButton("Select PDF")
        btn.setMinimumHeight(40)

        name = QtWidgets.QLabel("")
        name.setStyleSheet("color: #A8A8A8;")
        name.setMinimumWidth(280)
        name.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        row.addWidget(lbl)
        row.addWidget(btn)
        row.addWidget(name, 1)

        parent_layout.addLayout(row)

        setattr(self, btn_attr, btn)
        setattr(self, lbl_attr, name)

    def _set_status(self, text: str):
        self.lbl_status.setText(text)

    def _select_pdf(self, which: str):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not file_path:
            return

        base = os.path.basename(file_path)

        if which == "parent_1":
            self.files.parent_1 = file_path
            self.lbl_p1.setText(base)
            self.lbl_p1.setToolTip(file_path)
        elif which == "parent_2":
            self.files.parent_2 = file_path
            self.lbl_p2.setText(base)
            self.lbl_p2.setToolTip(file_path)
        elif which == "child":
            self.files.child = file_path
            self.lbl_child.setText(base)
            self.lbl_child.setToolTip(file_path)

        self._set_status(f"Selected: {base}")
        self.btn_run.setEnabled(self.files.all_selected())

    def run_merge(self):
        if not self.files.all_selected():
            QtWidgets.QMessageBox.warning(self, "Missing Files", "Please select all required PDFs.")
            return

        self._set_status("Processing PDFs…")
        QtWidgets.QApplication.processEvents()

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            df_p1 = extract_all_tables(self.files.parent_1)
            df_p2 = extract_all_tables(self.files.parent_2)
            df_parent = (
                pd.concat([df_p1, df_p2], ignore_index=True)
                if not df_p1.empty or not df_p2.empty
                else pd.DataFrame()
            )

            df_child = extract_all_tables(self.files.child)

            if df_parent.empty:
                QtWidgets.QMessageBox.critical(self, "Error", "Parent PDFs produced no data.")
                self._set_status("Parent PDFs produced no data.")
                return

            df_parent = rename_columns_parent(df_parent)
            df_child = rename_columns_child(df_child)

            ok, msg = ensure_required_columns(df_parent, df_child)
            if not ok:
                QtWidgets.QMessageBox.critical(self, "Error", msg)
                self._set_status(f"Error: {msg}")
                return

            df_merged = merge_parent_child(df_parent, df_child)
            df_expanded = expand_secondary_to_master_baby(df_merged)
            self.df_final = select_final_columns(df_expanded)

            self._update_table_view(self.df_final)
            self.btn_download.setEnabled(True)
            self._set_status("Done. Click Download Excel to save.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Processing failed:\n{e}")
            self._set_status(f"Error: {e}")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _update_table_view(self, df: pd.DataFrame):
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for _, row in df.iterrows():
            items = []
            for val in row.tolist():
                item = QtGui.QStandardItem("" if pd.isna(val) else str(val))
                item.setEditable(False)
                items.append(item)
            model.appendRow(items)

        self.tableView.setModel(model)

        # UX: better sizing/readability
        header = self.tableView.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def download_result(self):
        if self.df_final is None or self.df_final.empty:
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
            self.df_final.to_excel(save_file, index=False)
            QtWidgets.QMessageBox.information(self, "Success", f"Saved:\n{save_file}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Unable to save:\n{e}")

    def on_back(self):
        # stacked navigation is handled in app.py
        self.close()