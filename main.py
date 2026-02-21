from PyQt5 import QtCore, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Home")
        Dialog.setMinimumSize(900, 620)

        root = QtWidgets.QVBoxLayout(Dialog)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # -------------------------
        # App Bar
        # -------------------------
        appbar = QtWidgets.QFrame(Dialog)
        appbar.setObjectName("AppBar")
        appbar_layout = QtWidgets.QVBoxLayout(appbar)
        appbar_layout.setContentsMargins(18, 16, 18, 16)
        appbar_layout.setSpacing(6)

        self.titleLabel = QtWidgets.QLabel("XtractPDF", appbar)
        self.titleLabel.setObjectName("Title")

        self.instructionLabel = QtWidgets.QLabel(
            "PDF processing toolkit — extract invoice data and compare cargo manifests.",
            appbar
        )
        self.instructionLabel.setObjectName("Subtitle")

        appbar_layout.addWidget(self.titleLabel)
        appbar_layout.addWidget(self.instructionLabel)
        root.addWidget(appbar)

        # -------------------------
        # Overview / How it works
        # -------------------------
        overview = QtWidgets.QFrame(Dialog)
        overview.setObjectName("Card")
        ov_layout = QtWidgets.QVBoxLayout(overview)
        ov_layout.setContentsMargins(18, 18, 18, 18)
        ov_layout.setSpacing(8)

        ov_title = QtWidgets.QLabel("Quick Overview", overview)
        ov_title.setStyleSheet("font-size: 13pt; font-weight: 800; color: #FFFFFF;")

        ov_desc = QtWidgets.QLabel(
            "Use this tool to convert operational PDFs into clean Excel outputs. "
            "It supports table extraction, manifest merging, and export workflows.",
            overview
        )
        ov_desc.setWordWrap(True)
        ov_desc.setStyleSheet("color: #A8A8A8;")

        # small “pill” row
        pills = QtWidgets.QHBoxLayout()
        pills.setSpacing(10)
        pills.addWidget(self._pill("Fast exports"))
        pills.addWidget(self._pill("Excel ready (.xlsx)"))
        pills.addWidget(self._pill("Works offline"))
        pills.addStretch(1)

        ov_layout.addWidget(ov_title)
        ov_layout.addWidget(ov_desc)
        ov_layout.addLayout(pills)

        root.addWidget(overview)

        # -------------------------
        # Feature Cards
        # -------------------------
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(18)

        card1 = self._make_card(
            Dialog,
            title="Extract Invoice Data",
            desc="Turn invoice PDFs into structured Excel tables — ready for finance / ops workflows.",
            bullets=[
                "Extract tables from invoices",
                "Cleaned columns and rows",
                "Export to .xlsx for reporting",
            ],
            button_text="Open",
            button_obj_name="Extractinvoicbutton",
        )
        self.Extractinvoicbutton = card1.findChild(QtWidgets.QPushButton, "Extractinvoicbutton")

        card2 = self._make_card(
            Dialog,
            title="Compare Cargo Manifests",
            desc="Merge two parent manifests with a child manifest and generate final Master/Baby output.",
            bullets=[
                "Merge by HAWB",
                "Expand secondary tracking numbers",
                "Final column ordering + Excel export",
            ],
            button_text="Open",
            button_obj_name="pushButton_2",
        )
        self.pushButton_2 = card2.findChild(QtWidgets.QPushButton, "pushButton_2")

        row.addWidget(card1)
        row.addWidget(card2)
        root.addLayout(row)

        # -------------------------
        # Footer tip
        # -------------------------
        tip = QtWidgets.QLabel(
            "Tip: Best results come from PDFs with selectable text (not scanned images).",
            Dialog
        )
        tip.setStyleSheet("color: #8F8F8F; font-size: 10.5pt;")
        root.addWidget(tip)

        root.addStretch(1)

        QtCore.QMetaObject.connectSlotsByName(Dialog)

    # ---------- UI helpers ----------

    def _pill(self, text: str):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border: 1px solid #2C2C2C;
                padding: 6px 10px;
                border-radius: 999px;
                color: #CFCFCF;
                font-weight: 600;
            }
        """)
        return lbl

    def _make_card(self, parent, title: str, desc: str, bullets, button_text: str, button_obj_name: str):
        card = QtWidgets.QFrame(parent)
        card.setObjectName("Card")

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        t = QtWidgets.QLabel(title, card)
        t.setStyleSheet("font-size: 15pt; font-weight: 800; color: #FFFFFF;")

        d = QtWidgets.QLabel(desc, card)
        d.setWordWrap(True)
        d.setStyleSheet("color: #A8A8A8;")

        # bullet list
        bullet_box = QtWidgets.QVBoxLayout()
        bullet_box.setSpacing(6)
        for b in bullets:
            bullet = QtWidgets.QLabel(f"• {b}", card)
            bullet.setStyleSheet("color: #CFCFCF;")
            bullet_box.addWidget(bullet)

        btn = QtWidgets.QPushButton(button_text, card)
        btn.setObjectName(button_obj_name)
        btn.setMinimumHeight(42)

        layout.addWidget(t)
        layout.addWidget(d)
        layout.addLayout(bullet_box)
        layout.addStretch(1)
        layout.addWidget(btn)

        return card


if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QWidget()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())