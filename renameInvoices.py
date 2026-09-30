"""Reusable renamer; the CLI accepts a folder instead of a machine-specific drive."""
import argparse
from pathlib import Path

from invoice_core import (clean_path, extract_invoice_data, print_rename_results,
                          rename_invoices)

TARGET_FOLDER = "./invoices"
NAMING_FORMAT = "{date}_{seller}_{amount}"
UNKNOWN_PREFIX = "解析失败_"


class InvoiceRenamer:
    def __init__(self, folder_path, naming_format):
        self.folder_path = Path(folder_path)
        self.naming_format = naming_format

    def clean_text(self, text):
        return (text or "").replace(" ", "").replace("\u00a0", "")

    def extract_invoice_data(self, pdf_path):
        return extract_invoice_data(pdf_path)

    def rename(self):
        results = rename_invoices(self.folder_path, self.naming_format)
        print_rename_results(results)
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量重命名 PDF 电子发票")
    parser.add_argument("folder", nargs="?", default=TARGET_FOLDER)
    parser.add_argument("--format", default=NAMING_FORMAT)
    args = parser.parse_args()
    try:
        InvoiceRenamer(clean_path(args.folder), args.format).rename()
    except (ValueError, OSError) as exc:
        parser.exit(1, f"错误: {exc}\n")
