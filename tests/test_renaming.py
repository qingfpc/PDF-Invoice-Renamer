import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import reportlab

from invoice_core import (InvoiceParseError, clean_path, format_invoice_name,
                          read_invoice_data, rename_invoices)
from renameInvoices import InvoiceRenamer


pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
pdfmetrics.registerFont(TTFont("TestVera", str(Path(reportlab.__file__).parent / "fonts" / "Vera.ttf")))
STANDARD = (
    "发票代码：123456789012\n发票号码：12345678\n开票日期：2026年10月01日\n"
    "名称：购买公司\n名称：销售公司\n价税合计 (小写) ￥123.45"
)


def make_invoice(path, text=STANDARD):
    document = canvas.Canvas(str(path), pagesize=(595, 300))
    document.setFont("STSong-Light", 12)
    for index, line in enumerate(text.splitlines()):
        y = 280 - index * 24
        if "−" in line:
            # STSong has no U+2212 glyph; embed a font that preserves this sign.
            prefix, suffix = line.split("−", 1)
            document.drawString(20, y, prefix)
            x = 20 + pdfmetrics.stringWidth(prefix, "STSong-Light", 12)
            document.setFont("TestVera", 12)
            document.drawString(x, y, "−")
            x += pdfmetrics.stringWidth("−", "TestVera", 12)
            document.setFont("STSong-Light", 12)
            document.drawString(x, y, suffix)
        else:
            document.drawString(20, y, line)
    document.save()


class RenamingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def invoice(self, text=STANDARD, filename="original.pdf"):
        path = self.folder / filename
        make_invoice(path, text)
        return path

    def test_standard_fields_include_buyer(self):
        result = read_invoice_data(self.invoice())
        self.assertEqual(result, {
            "code": "123456789012", "number": "12345678", "date": "20261001",
            "amount": "123.45", "seller": "销售公司", "buyer": "购买公司",
        })

    def test_signed_grouped_and_zero_amounts(self):
        for raw, expected in [("1,234.56", "1234.56"), ("-123.45", "-123.45"),
                              ("−123.45", "-123.45"), ("0", "0.00"), ("123", "123.00")]:
            with self.subTest(raw=raw):
                self.assertEqual(read_invoice_data(self.invoice(STANDARD.replace("123.45", raw)))["amount"], expected)

    def test_malformed_amount_is_missing_instead_of_zero_or_prefix(self):
        for raw in ["1,23.45", "123.456", "1.2.3", "--100"]:
            with self.subTest(raw=raw):
                data = read_invoice_data(self.invoice(STANDARD.replace("123.45", raw)))
                self.assertIsNone(data["amount"])
                with self.assertRaises(InvoiceParseError):
                    format_invoice_name(data, "{amount}_{seller}")

    def test_noninvoice_is_not_renamed(self):
        original = self.invoice("Ordinary document")
        original_bytes = original.read_bytes()
        results = rename_invoices(self.folder, "{date}_{seller}_{amount}")
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(list(self.folder.iterdir()), [original])

    def test_missing_fields_and_invalid_date_preserve_original(self):
        original = self.invoice(STANDARD.replace("2026年10月01日", "2026年99月99日"))
        result = rename_invoices(self.folder, "{date}_{seller}_{amount}")[0]
        self.assertEqual(result.status, "failed")
        self.assertTrue(original.exists())

    def test_invoice_date_has_priority_over_other_dates(self):
        data = read_invoice_data(self.invoice("订单日期：2025年01月01日\n" + STANDARD))
        self.assertEqual(data["date"], "20261001")

    def test_negative_sign_before_currency_is_preserved(self):
        data = read_invoice_data(self.invoice(STANDARD.replace("￥123.45", "-￥123.45")))
        self.assertEqual(data["amount"], "-123.45")

    def test_full_digital_number_does_not_require_invoice_code(self):
        original = self.invoice(STANDARD.replace("发票代码：123456789012\n", "")
                                .replace("12345678", "12345678901234567890"))
        data = read_invoice_data(original)
        self.assertIsNone(data["code"])
        self.assertEqual(rename_invoices(self.folder, "{number}")[0].status, "renamed")
        self.assertEqual(rename_invoices(self.folder, "{code}_{number}")[0].status, "failed")

    def test_spaced_labels_and_complete_english_seller(self):
        text = STANDARD.replace("发票号码", "发 票 号 码").replace("名称", "名 称")
        text = text.replace("销售公司", "ABC (China) Co., Ltd.")
        data = read_invoice_data(self.invoice(text))
        self.assertEqual(data["number"], "12345678")
        self.assertEqual(data["seller"], "ABC (China) Co., Ltd.")

    def test_field_words_inside_company_names_are_not_truncated(self):
        text = STANDARD.replace("销售公司", "杭州电话地址名称科技有限公司")
        data = read_invoice_data(self.invoice(text))
        self.assertEqual(data["seller"], "杭州电话地址名称科技有限公司")

    def test_roles_override_name_order(self):
        text = STANDARD.replace("名称：购买公司\n名称：销售公司",
                                "销售方 名称：销售公司\n购买方 名称：购买公司")
        data = read_invoice_data(self.invoice(text))
        self.assertEqual(data["buyer"], "购买公司")
        self.assertEqual(data["seller"], "销售公司")

    def test_two_names_on_one_line_stop_at_following_field(self):
        text = STANDARD.replace("名称：购买公司\n名称：销售公司",
                                "购买方 名称：购买公司 销售方 名称：销售公司 纳税人识别号：123")
        data = read_invoice_data(self.invoice(text))
        self.assertEqual(data["buyer"], "购买公司")
        self.assertEqual(data["seller"], "销售公司")

    def test_collision_names_stay_stable_across_repeated_runs(self):
        self.invoice(filename="a.pdf")
        self.invoice(STANDARD.replace("12345678\n", "87654321\n"), "b.PDF")
        first = rename_invoices(self.folder, "{date}_{seller}_{amount}")
        self.assertEqual([r.status for r in first], ["renamed", "renamed"])
        expected = sorted(p.name for p in self.folder.iterdir())
        for _ in range(3):
            self.assertTrue(all(r.status == "skipped" for r in rename_invoices(self.folder, "{date}_{seller}_{amount}")))
            self.assertEqual(sorted(p.name for p in self.folder.iterdir()), expected)
        # Removing the first slot must not make the second file churn either.
        (self.folder / "20261001_销售公司_123.45.pdf").unlink()
        self.assertEqual(rename_invoices(self.folder, "{date}_{seller}_{amount}")[0].status, "skipped")

    def test_legacy_class_sanitizes_every_collision_name(self):
        self.invoice(filename="a.pdf")
        self.invoice(filename="b.pdf")
        renamer = InvoiceRenamer(self.folder, "invoice:/{number}")
        with contextlib.redirect_stdout(io.StringIO()):
            results = renamer.rename()
        self.assertTrue(all(r.status == "renamed" for r in results))
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()),
                         ["invoice12345678.pdf", "invoice12345678_1.pdf"])

    def test_path_quotes_preserve_apostrophes(self):
        self.assertEqual(clean_path('"D:\\Invoices\\O\'Brien"'), "D:\\Invoices\\O'Brien")
        self.assertEqual(clean_path("D:\\Invoices\\O'Brien"), "D:\\Invoices\\O'Brien")

    def test_invalid_template_preserves_original(self):
        original = self.invoice()
        result = rename_invoices(self.folder, "{missing}")[0]
        self.assertEqual(result.status, "failed")
        self.assertTrue(original.exists())

    def test_corrupt_and_scanned_files_do_not_stop_the_batch(self):
        (self.folder / "corrupt.pdf").write_bytes(b"not a PDF")
        self.invoice("", "blank.pdf")
        self.invoice(filename="valid.pdf")
        results = rename_invoices(self.folder, "{number}")
        self.assertEqual(sum(r.status == "failed" for r in results), 2)
        self.assertEqual(sum(r.status == "renamed" for r in results), 1)


if __name__ == "__main__":
    unittest.main()
