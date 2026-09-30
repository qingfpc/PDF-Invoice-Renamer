import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from PIL import Image

import invoiceMaster
import mergeInvoices
from invoice_merge import (merge_pdf_files, print_merge_result,
                           resolve_output_path)
from invoice_core import InvoiceParseError, read_invoice_data


def make_pages(path, colors=((1, 0, 0),), rotation=0, encrypted=False):
    with fitz.open() as document:
        for index, color in enumerate(colors):
            page = document.new_page(width=595, height=300)
            page.insert_text((20, 40), f"INVOICE-PAGE-{index + 1}")
            stamp = page.add_rect_annot(fitz.Rect(300, 100, 430, 180))
            stamp.set_colors(stroke=color, fill=color)
            stamp.update()
            page.set_rotation(rotation)
        options = {"encryption": fitz.PDF_ENCRYPT_AES_256, "user_pw": "secret", "owner_pw": "owner"} if encrypted else {}
        document.save(path, **options)


def color_count(page, channel):
    pixmap = page.get_pixmap(alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return sum(count for count, color in image.getcolors(pixmap.width * pixmap.height)
               if color[channel] > 200 and all(color[i] < 80 for i in range(3) if i != channel))


class MergingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_odd_even_and_single_page_layout(self):
        for count in (1, 2, 3):
            with self.subTest(count=count):
                folder = self.folder / str(count)
                folder.mkdir()
                for index in range(count):
                    make_pages(folder / f"{index}.pdf")
                result = merge_pdf_files(folder, folder / "merged.pdf")
                self.assertFalse(result.failures)
                self.assertEqual(result.merged_pages, count)
                with fitz.open(result.output) as output:
                    self.assertEqual(len(output), (count + 1) // 2)
                    self.assertEqual(sum(len(p.get_images()) for p in output), count)
                    self.assertTrue(all(p.rect.width == 595 and p.rect.height == 842 for p in output))

    def test_every_source_page_and_its_annotation_is_retained(self):
        make_pages(self.folder / "multipage.pdf", ((1, 0, 0), (0, 0, 1)))
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertEqual(result.input_pages, 2)
        self.assertEqual(result.merged_pages, 2)
        with fitz.open(result.output) as output:
            self.assertEqual(len(output[0].get_images()), 2)
            self.assertGreater(color_count(output[0], 0), 1000)
            self.assertGreater(color_count(output[0], 2), 1000)

    def test_rotated_page_preserves_annotation(self):
        make_pages(self.folder / "rotated.PDF", rotation=90)
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertFalse(result.failures)
        with fitz.open(result.output) as output:
            self.assertGreater(color_count(output[0], 0), 100)

    def test_image_only_scan_merges_but_cannot_be_renamed(self):
        source = self.folder / "scan.pdf"
        with fitz.open() as original:
            page = original.new_page(width=595, height=300)
            page.draw_rect(fitz.Rect(300, 100, 430, 180), color=(1, 0, 0), fill=(1, 0, 0))
            pixmap = page.get_pixmap(alpha=False)
            with fitz.open() as scan:
                scan.new_page(width=595, height=300).insert_image(page.rect, pixmap=pixmap)
                scan.save(source)
        with self.assertRaises(InvoiceParseError):
            read_invoice_data(source)
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertFalse(result.failures)
        with fitz.open(result.output) as output:
            self.assertGreater(color_count(output[0], 0), 1000)

    def test_all_corrupt_produces_no_blank_output_or_success_message(self):
        (self.folder / "broken.pdf").write_bytes(b"bad")
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertIsNone(result.output)
        self.assertEqual(len(result.failures), 1)
        self.assertFalse((self.folder / "merged.pdf").exists())
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            print_merge_result(result)
        self.assertNotIn("合并成功", stream.getvalue())

    def test_partial_failure_has_no_empty_slot_and_is_reported(self):
        (self.folder / "a-broken.pdf").write_bytes(b"bad")
        make_pages(self.folder / "b-valid.pdf")
        make_pages(self.folder / "c-valid.pdf")
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertEqual(result.input_files, 3)
        self.assertEqual(result.merged_pages, 2)
        self.assertEqual(len(result.failures), 1)
        with fitz.open(result.output) as output:
            self.assertEqual(len(output), 1)
            self.assertEqual(len(output[0].get_images()), 2)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            print_merge_result(result)
        self.assertIn("部分完成", stream.getvalue())
        self.assertNotIn("合并成功", stream.getvalue())

    def test_encrypted_pdf_is_reported_without_open_handle_leak(self):
        source = self.folder / "encrypted.pdf"
        make_pages(source, encrypted=True)
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertIn("加密", result.failures[0].reason)
        self.assertIsNone(result.output)
        source.rename(self.folder / "released.pdf")

    def test_no_input_and_directory_named_pdf_are_ignored(self):
        (self.folder / "directory.pdf").mkdir()
        result = merge_pdf_files(self.folder, self.folder / "merged.pdf")
        self.assertEqual(result.merged_pages, 0)
        self.assertIsNone(result.output)

    def test_existing_output_is_never_overwritten(self):
        source = self.folder / "original.pdf"
        make_pages(source)
        before = source.read_bytes()
        with self.assertRaises(FileExistsError):
            merge_pdf_files(self.folder, source)
        self.assertEqual(source.read_bytes(), before)

    def test_invalid_output_parent_leaves_no_partial_pdf(self):
        make_pages(self.folder / "original.pdf")
        blocked_parent = self.folder / "blocked"
        blocked_parent.write_bytes(b"preserve")
        with self.assertRaises(OSError):
            merge_pdf_files(self.folder, blocked_parent / "merged.pdf")
        self.assertEqual(blocked_parent.read_bytes(), b"preserve")
        self.assertFalse(list(self.folder.glob(".invoice-*")))

    def test_custom_outputs_are_excluded_when_merging_again(self):
        make_pages(self.folder / "original.pdf")
        for name in ("custom.pdf", "custom_1.pdf", "custom_2.pdf"):
            result = merge_pdf_files(self.folder, self.folder / name)
            self.assertEqual(result.input_files, 1)
            self.assertEqual(result.merged_pages, 1)
            self.assertFalse(result.failures)

    def test_output_directory_or_filename_and_conflicts(self):
        self.assertEqual(resolve_output_path("", self.folder, "default.pdf"), self.folder / "default.pdf")
        custom = self.folder / "O'Brien" / "custom.pdf"
        self.assertEqual(resolve_output_path(str(custom), self.folder, "default.pdf"), custom)
        custom.parent.mkdir()
        custom.write_bytes(b"preserve")
        self.assertEqual(resolve_output_path(str(custom), self.folder, "default.pdf"), custom.with_name("custom_1.pdf"))
        self.assertEqual(custom.read_bytes(), b"preserve")

    def test_both_interactive_mergers_keep_stamps_and_repeat_safely(self):
        make_pages(self.folder / "original.pdf")
        with patch("builtins.input", return_value=""), contextlib.redirect_stdout(io.StringIO()):
            first = invoiceMaster.run_merger(self.folder)
        with patch("builtins.input", side_effect=[str(self.folder), "", ""]), contextlib.redirect_stdout(io.StringIO()):
            second = mergeInvoices.merge_invoices()
        with patch("builtins.input", side_effect=[str(self.folder), "", ""]), contextlib.redirect_stdout(io.StringIO()):
            third = mergeInvoices.merge_invoices()
        for result in (first, second, third):
            self.assertEqual(result.merged_pages, 1)
            self.assertFalse(result.failures)
            with fitz.open(result.output) as output:
                self.assertGreater(color_count(output[0], 0), 1000)
        self.assertNotEqual(second.output, third.output)


if __name__ == "__main__":
    unittest.main()
