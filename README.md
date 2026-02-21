# PDF-Scrapper (XtractPDF)

A Windows desktop application built with **Python + PyQt5** for extracting structured data from PDF invoices and comparing cargo manifests. Designed for efficiency, accuracy, and usability, the app uses background threading to keep the UI responsive and exports results directly to Excel.

---

## 🚀 Features

### 1) Extract Invoice Data → Excel
- Select a PDF invoice.
- Extracts key fields:
  - Marks / Container Number
  - Description
  - Commodity / HS Code
  - Gross Mass
  - Item Price
- Uses **Camelot** for table extraction and **regex parsing**.
- Runs in a background thread (no UI freeze).
- Exports results to `.xlsx` using **pandas + openpyxl**.

### 2) Compare Cargo Manifests (Parent vs Child) → Excel
- Select **Parent PDF 1**, **Parent PDF 2**, and **Child PDF**.
- Extracts tables across all pages using **pdfplumber**.
- Merges manifests by **HAWB**.
- Normalizes messy PDF headers (e.g., `HAWB\nNumber`, `HAWB\nShipment`, `Secondary Tracking Numbers`).
- Expands secondary tracking numbers into **Master/Baby rows**:
  - **Master** = original HAWB
  - **Baby** = each secondary number becomes a row
- Preview results in the UI before exporting to `.xlsx`.

---

## 🛠 Tech Stack
- **Python 3.10+**
- **PyQt5** (UI framework)
- **Camelot** (PDF table extraction)
- **pdfplumber** (PDF parsing)
- **pandas + openpyxl** (Excel export)
- **Regex** (data parsing)

---

## 📂 Project Structure

```
PDF-Scrapper/
├── app.py                   # Main app (QStackedWidget navigation)
├── main.py                  # Main menu UI
├── CompareCargoManifests.py # Cargo manifest compare + merge + export
├── ExtractInvoiceData.py    # Invoice extraction + threaded processing + export
├── README.md
└── .gitignore
```

---

## ⚙️ Installation (Windows)

1) Clone the repository:
```bash
git clone https://github.com/Deathbot545/PDF-Scrapper.git
cd PDF-Scrapper
```

2) Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3) Upgrade pip:
```bash
python -m pip install --upgrade pip
```

4) Install dependencies:
```bash
pip install PyQt5 pandas pdfplumber camelot-py openpyxl
```

> If you plan to process scanned PDFs (images), OCR is required. This repo currently assumes text-based PDFs.

---

## ▶️ How to Run
```bash
python app.py
```

---

## 📖 Usage

### Extract Invoice Data
1. Launch the app.
2. Choose **Extract Invoice Data**.
3. Click **Select PDF to Convert** and pick the invoice PDF.
4. Wait until processing completes.
5. Click **Download Result** to export to Excel.

### Compare Cargo Manifests
1. Launch the app.
2. Choose **Compare Cargo Manifests**.
3. Select **Parent PDF 1**, **Parent PDF 2**, and **Child PDF**.
4. Click **Run** to process and preview results.
5. Click **Download Excel** to export to Excel.

---

## 🧯 Troubleshooting

### 1) `ModuleNotFoundError: No module named 'PyQt5'`
Make sure you are using the **venv python**, not your global python.

```bash
where python
python -c "import PyQt5; print('PyQt5 OK')"
```

If `where python` doesn’t point to your `venv`, activate it again:
```bash
venv\Scripts\activate
```

### 2) Camelot not detecting tables
If invoice PDFs don’t have table lines, switch Camelot mode in `ExtractInvoiceData.py`:
- From `flavor="lattice"` to `flavor="stream"`

### 3) pdfplumber returns empty tables
Some PDFs are scanned images, not text tables. OCR would be required (not implemented here).

---

## 🔒 Repo Hygiene (Important)

Do **NOT** commit:
- `venv/`
- `.env`
- client PDFs
- generated Excel outputs

### Recommended `.gitignore`
```gitignore
venv/
.venv/
__pycache__/
*.pyc

.env

PDF/
*.pdf
*.xlsx

dist/
build/
*.spec
```

### If you accidentally committed `venv/` already
This removes it from Git tracking (keeps it on your PC):
```bash
git rm -r --cached venv
git add .gitignore
git commit -m "Remove venv from repo"
git push
```

### Optional: Remove large files from GitHub history (advanced)
```bash
python -m pip install git-filter-repo
git filter-repo --path venv --invert-paths
git push --force --all
git push --force --tags
```

---

## 📌 Notes
- This project targets Windows workflows and is optimized for quick “select → preview → export” operations.
- For scanned/image-based PDFs, consider adding an OCR pipeline in the future.
