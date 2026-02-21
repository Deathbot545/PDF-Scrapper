# PDF-Scrapper (XtractPDF)

A Windows desktop application built with **Python + PyQt5** for extracting structured data from PDF invoices and comparing cargo manifests. Designed for efficiency, accuracy, and usability, the app leverages background threading to keep the UI responsive and exports results directly to Excel.

---

## 🚀 Features

### 1. Extract Invoice Data → Excel
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

### 2. Compare Cargo Manifests (Parent vs Child) → Excel
- Select **Parent PDF 1**, **Parent PDF 2**, and **Child PDF**.
- Extracts tables across all pages using **pdfplumber**.
- Merges manifests by **HAWB**.
- Normalizes messy PDF headers (e.g., `HAWB\nNumber`, `HAWB\nShipment`, `Secondary Tracking Numbers`).
- Expands secondary tracking numbers into **Master/Baby rows**:
  - Master = original HAWB  
  - Baby = each secondary number becomes a row  
- Preview results in the UI before exporting to `.xlsx`.

---

## 🛠 Tech Stack
- **Python 3**
- **PyQt5** (UI framework)
- **Camelot** (PDF table extraction)
- **pdfplumber** (PDF parsing)
- **pandas + openpyxl** (Excel export)
- **Regex** (data parsing)

---

## 📂 Project Structure
PDF-Scrapper/ │ ├── app.py                  
# Main QStackedWidget navigation ├── main.py                 
# Main menu UI ├── CompareCargoManifests.py # Manifest logic + UI ├── ExtractInvoiceData.py    
# Invoice extraction logic + UI

---

## ⚙️ Installation (Windows)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PDF-Scrapper.git
   cd PDF-Scrapper
   
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   
3.Upgrade pip:
   ```bash
   python -m pip install --upgrade pip

4.Install Dependency
   ```bash
   pip install PyQt5 pandas pdfplumber camelot-py openpyx

5.How to Run
   ```bash
   python app.py


📖 Usage
Extract Invoice Data
- Launch the app.
- Select a PDF invoice.
- Preview extracted fields.
- Export results to Excel.
Compare Cargo Manifests
- Select Parent PDF 1, Parent PDF 2, and Child PDF.
- Preview merged and normalized tables.
- Export results to Excel.
