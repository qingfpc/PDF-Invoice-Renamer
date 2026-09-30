"""Exercise complete CLI processes against real, temporary PDF files."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

from tests.test_renaming import STANDARD, make_invoice

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "中文 O'Brien"
        self.folder.mkdir()

    def run_script(self, filename, answers=None, arguments=()):
        environment = dict(os.environ, PYTHONUTF8="1")
        executable_names = {"invoiceMaster.py": "InvoiceHelper_AllInOne.exe",
                            "invoiceTool.py": "InvoiceRenamer_Only.exe",
                            "mergeInvoices.py": "InvoiceMerger_Only.exe"}
        executable_dir = environment.get("INVOICE_TEST_EXE_DIR")
        if executable_dir and filename in executable_names:
            executable = Path(executable_dir) / executable_names[filename]
            self.assertTrue(executable.is_file(), str(executable))
            command = [str(executable), *arguments]
            environment.pop("PYTHONPATH", None)
            environment.pop("PYTHONHOME", None)
        else:
            command = [sys.executable, str(ROOT / filename), *arguments]
        completed = subprocess.run(command,
                                   input=answers, capture_output=True, encoding="utf-8",
                                   env=environment, cwd=self.folder, timeout=90)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        return completed

    def test_all_in_one_renames_merges_and_repeats(self):
        make_invoice(self.folder / "a.pdf")
        make_invoice(self.folder / "b.PDF", STANDARD.replace("12345678\n", "87654321\n"))
        output = self.folder / "自定义打印.pdf"
        answers = f'"{self.folder}"\ny\n1\ny\n"{output}"\n\n'
        first = self.run_script("invoiceMaster.py", answers)
        self.assertIn("成功: 2, 失败: 0", first.stdout)
        self.assertIn("合并成功", first.stdout)
        with fitz.open(output) as document:
            self.assertEqual(len(document), 1)
            self.assertEqual(len(document[0].get_images()), 2)
        originals = {p.name: p.read_bytes() for p in self.folder.glob("20261001*.pdf")}
        second = self.run_script("invoiceMaster.py", answers)
        self.assertIn("成功: 0, 失败: 0", second.stdout)
        self.assertIn("合并成功", second.stdout)
        self.assertTrue(output.with_name("自定义打印_1.pdf").exists())
        self.assertEqual({p.name: p.read_bytes() for p in self.folder.glob("20261001*.pdf")}, originals)

    def test_standalone_renamer_preserves_noninvoice(self):
        make_invoice(self.folder / "valid.pdf")
        unrelated = self.folder / "keep.pdf"
        make_invoice(unrelated, "Ordinary document")
        before = unrelated.read_bytes()
        completed = self.run_script("invoiceTool.py", f'"{self.folder}"\n1\n\n\n')
        self.assertIn("成功: 1, 失败: 1", completed.stdout)
        self.assertEqual(unrelated.read_bytes(), before)

    def test_standalone_merger_accepts_filename(self):
        make_invoice(self.folder / "original.pdf")
        output = self.folder / "新目录" / "custom.pdf"
        completed = self.run_script("mergeInvoices.py", f'"{self.folder}"\n"{output}"\n\n')
        self.assertIn("合并成功", completed.stdout)
        self.assertTrue(output.exists())

    def test_reusable_renamer_cli_accepts_folder_and_format(self):
        make_invoice(self.folder / "original.pdf")
        self.run_script("renameInvoices.py", arguments=(str(self.folder), "--format", "{number}"))
        self.assertTrue((self.folder / "12345678.pdf").exists())

    def test_blank_input_does_not_select_current_directory(self):
        make_invoice(self.folder / "original.pdf")
        completed = self.run_script("invoiceTool.py", f"\n{self.folder}\n1\n\n\n")
        self.assertIn("路径不存在或不是文件夹", completed.stdout)


if __name__ == "__main__":
    unittest.main()
