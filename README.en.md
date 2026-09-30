[English](README.en.md) | [简体中文](README.md)

# PDF Invoice Helper (Renamer & Merger)

This is a lightweight Python-based tool designed to help finance staff, administrators, or developers batch process PDF electronic invoices.

It not only automatically extracts **key information** (such as date, seller, amount, invoice number, etc.) to rename files but also intelligently **merges and layouts** multiple invoices into a single PDF file (two invoices per A4 page), greatly simplifying the reimbursement printing process.

## ✨ Features

### 1. Smart Renaming
* **Auto Extraction**: Uses `pdfplumber` to extract text from PDFs, identifying invoice codes, numbers, dates, amounts, and sellers.
* **Custom Formats**: Supports multiple renaming formats (e.g., `Date_Seller_Amount` or `Code_Number`).
* **Conflict Prevention**: Adds a suffix for collisions and keeps names stable on repeat runs. Missing required fields preserve the original name.

### 2. A4 Layout Merging
* **Smart Layout**: Arranges two invoices vertically on a single A4 page (2-up layout) to save paper.
* **All Pages**: Processes every page of each PDF; an odd final page occupies the upper half.
* **Visible Stamps**: Both tools use 216 DPI image rendering, including annotations. Output text is no longer selectable.
* **Honest Results**: Reports partial failures and creates no blank output when every input fails. Existing bundles are skipped.
* **Custom Output**: Accepts a directory or full PDF filename, creates directories, and adds suffixes instead of overwriting existing files.

### 3. Easy to Use
* **Batch Processing**: Process all PDF files in a folder with one click.
* **Out-of-the-Box**: A pre-packaged `.exe` program is provided, requiring no Python environment to run on Windows.

---

## 🚀 Quick Start (For Users)

If you are not a developer and just want to use the tool, follow these steps:

1.  **Download**:
    * Go to the [Releases Page](https://github.com/qingfpc/PDF-Invoice-Renamer/releases/latest).
    * Choose the tool that fits your needs:
        * `InvoiceHelper_AllInOne.exe`: **All-in-One Helper** for both auto-renaming and A4 layout merging (Recommended).
        * `InvoiceRenamer_Only.exe`: **Renamer Tool** for automatic renaming only.
        * `InvoiceMerger_Only.exe`: **Merger Tool** for A4 layout and PDF merging only.

2. **Run**:
    * Double-click the `.exe` file.
    * Follow the prompts to input (or drag and drop) your invoice folder path.

---

## 💻 Developer Guide

If you want to view the source code or contribute, please refer to the following instructions.

### 📂 Project Structure

* `invoiceMaster.py`: **[Recommended] Main Program**. Combines renaming and merging features with a full CLI.
* `mergeInvoices.py`: **Standalone Merger**. Contains only the A4 layout and merging logic.
* `renameInvoices.py`: **Reusable Class and CLI** with folder and format arguments.
* `invoice_core.py`: Shared parsing, validation, and repeatable renaming.
* `invoice_merge.py`: Shared multi-page layout and structured results.
* `tests/`: PDF regression and complete CLI process tests.
* `invoiceTool.py`: (Legacy) Script for renaming only.

### 🔧 Dependencies

Validated on Windows 11 with Python 3.12. Use a project virtual environment; dependency versions are recorded in the requirements files and constraints.txt.

1.  Clone the repository:
    ```powershell
    git clone https://github.com/qingfpc/PDF-Invoice-Renamer.git
    ```

2.  Create an environment and install dependencies:
    ```powershell
    cd PDF-Invoice-Renamer
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    ```

3.  Run the script:
    ```powershell
    .\.venv\Scripts\python.exe invoiceMaster.py
    ```

### 📦 How to Build EXE

If you modify the code and want to repackage it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pwsh -NoLogo -NoProfile -File .\build.ps1
```

The script builds all three EXEs in `dist/` using the release names listed above. Build outputs are ignored by Git.

### Tests and module usage

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe renameInvoices.py "D:\Invoices" --format "{number}_{amount}"
```

After building, run the same interactive tests against all three EXEs:

```powershell
$env:INVOICE_TEST_EXE_DIR = (Join-Path (Get-Location) 'dist')
.\.venv\Scripts\python.exe -m unittest tests.test_cli -v
Remove-Item Env:\INVOICE_TEST_EXE_DIR
```

Tests create temporary PDFs and perform real parsing, rendering, and file operations. Personal invoices are untouched.
The `InvoiceRenamer` class remains available. `extract_invoice_data()` returns `None` for unrecognized documents;
missing fields on recognized invoices are also `None`, never fabricated zero amounts.
For full-digital invoices without a code, choose a format using `{number}` instead of `{code}`.

---

## 📝 Supported Renaming Formats

The tool comes with several common formats. You can easily add new ones in the `PRESET_FORMATS` dictionary in the code:

* **Format 1**: `{date}_{seller}_{amount}` (e.g., `20231225_JD_299.00.pdf`)
* **Format 2**: `{seller}_{date}_{amount}` (e.g., `JD_20231225_299.00.pdf`)
* **Format 3**: `{code}_{number}` (e.g., `033001234567_12345678.pdf`)
* **Format 4**: `{amount}_{seller}` (e.g., `299.00_JD.pdf`)

## ⚠️ Limitations

* **Standard E-Invoices Only**: Currently optimized for Chinese VAT electronic invoices. Non-standard receipts or itineraries may not be extracted accurately.
* **No OCR Support**: If the PDF is a scanned image (text cannot be selected), renaming cannot extract information, but merging for printing is supported.

## 📄 License

MIT License
