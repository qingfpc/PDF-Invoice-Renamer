[English](README.en.md) | [简体中文](README.md)

# PDF Invoice Helper (Renamer & Merger)

This is a lightweight Python-based tool designed to help finance staff, administrators, or developers batch process PDF electronic invoices.

It not only automatically extracts **key information** (such as date, seller, amount, invoice number, etc.) to rename files but also intelligently **merges and layouts** multiple invoices into a single PDF file (two invoices per A4 page), greatly simplifying the reimbursement printing process.

## ✨ Features

### 1. Smart Renaming
* **Auto Extraction**: Uses `pdfplumber` to extract text from PDFs, identifying invoice codes, numbers, dates, amounts, and sellers.
* **Custom Formats**: Supports multiple renaming formats (e.g., `Date_Seller_Amount` or `Code_Number`).
* **Conflict Prevention**: Automatically adds a sequence number if the target filename already exists.

### 2. A4 Layout Merging
* **Smart Layout**: Arranges two invoices vertically on a single A4 page (2-up layout) to save paper.
* **Single Page Handling**: If there is an odd number of invoices, the last page will contain the invoice in the top half.
* **Custom Output**: Supports exporting the merged file to a specified directory.

### 3. Easy to Use
* **Batch Processing**: Process all PDF files in a folder with one click.
* **Out-of-the-Box**: A pre-packaged `.exe` program is provided, requiring no Python environment to run on Windows.

---

## 🚀 Quick Start (For Users)

If you are not a developer and just want to use the tool, follow these steps:

1.  **Download**:
    * Go to the [Releases Page](https://github.com/qingfpc/PDF-Invoice-Renamer/releases/latest).
    * Download the latest executable file (e.g., `InvoiceHelper.exe`).

2.  **Run**:
    * Double-click `InvoiceHelper.exe`.
    * **Step 1**: Input (or drag and drop) the folder path containing your invoices.
    * **Step 2**: Choose whether to rename. If yes, select a format format (e.g., input `1` for `Date_Seller_Amount`).
    * **Step 3**: Choose whether to merge PDFs. Confirm, and the program will generate an A4 layout PDF containing all invoices.

3.  **Result**:
    * Your files will be renamed cleanly, and a new file named `Invoice_Collection_Timestamp.pdf` will be created for easy printing.

---

## 💻 Developer Guide

If you want to view the source code or contribute, please refer to the following instructions.

### 📂 Project Structure

* `invoice_master.py`: **[Recommended] Main Program**. Combines renaming and merging features with a full CLI.
* `invoice_merger.py`: **Standalone Merger**. Contains only the A4 layout and merging logic.
* `renameInvoices.py`: **Core Renaming Logic**. Encapsulates the PDF parsing class.
* `invoiceTool.py`: (Legacy) Script for renaming only.

### 🔧 Dependencies

This project is developed using Python 3.x.

1.  Clone the repository:
    ```bash
    git clone [https://github.com/qingfpc/PDF-Invoice-Renamer.git](https://github.com/qingfpc/PDF-Invoice-Renamer.git)
    ```

2.  Install dependencies (Added `pymupdf` for merging):
    ```bash
    pip install pdfplumber pymupdf
    ```

3.  Run the script:
    ```bash
    python invoice_master.py
    ```

### 📦 How to Build EXE

If you modify the code and want to repackage it:

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Build command (for the master script):
    ```bash
    pyinstaller --onefile --name InvoiceHelper invoice_master.py
    ```

---

## 📝 Supported Renaming Formats

The tool comes with several common formats. You can easily add new ones in the `PRESET_FORMATS` dictionary in the code:

* **Format 1**: `{date}_{seller}_{amount}` (e.g., `20231225_JD_299.00.pdf`)
* **Format 2**: `{seller}_{date}_{amount}` (e.g., `JD_20231225_299.00.pdf`)
* **Format 3**: `{code}_{number}` (e.g., `033001234567_12345678.pdf`)
* **Format 4**: `{amount}_{seller}` (e.g., `299.00_JD.pdf`)

## ⚠️ Limitations

* **Standard E-Invoices Only**: Currently optimized for Chinese VAT electronic invoices. Non-standard receipts or itineraries may not be extracted accurately.
* **No OCR Support**: If the PDF is a scanned image (text cannot be selected), this tool cannot extract information.

## 📄 License

MIT License