"""Shared invoice parsing and safe, repeatable batch renaming."""

import re
import string
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pdfplumber


PRESET_FORMATS = {
    "1": {"desc": "日期_销售方_金额", "fmt": "{date}_{seller}_{amount}"},
    "2": {"desc": "销售方_日期_金额", "fmt": "{seller}_{date}_{amount}"},
    "3": {"desc": "发票代码_发票号码", "fmt": "{code}_{number}"},
    "4": {"desc": "金额_销售方", "fmt": "{amount}_{seller}"},
}
INVOICE_FIELDS = {"date", "code", "number", "amount", "seller", "buyer"}
BUNDLE_MARKER = "invoice-helper:merged"


class InvoiceParseError(ValueError):
    """The document or the requested invoice fields could not be recognized."""


class MergedDocumentError(InvoiceParseError):
    """Generated print bundles must not be renamed or merged again."""


@dataclass
class RenameResult:
    source: Path
    status: str
    destination: Optional[Path] = None
    reason: str = ""


def clean_path(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def clean_filename(value):
    value = re.sub(r'[\x00-\x1f\\/*?:"<>|]', "", value).strip().rstrip(". ")
    if not value:
        raise ValueError("清理后文件名为空")
    # Windows also reserves these names when an extension follows them.
    if re.fullmatch(r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", value.split(".")[0], re.I):
        value = "_" + value
    return value


def is_bundle_name(path):
    return path.name.startswith("发票合集_") or path.name == "排版后发票合集.pdf"


def list_pdf_files(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError("输入路径必须是存在的文件夹")
    return sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
        key=lambda p: p.name.casefold(),
    )


def _label(word):
    return r"\s*".join(re.escape(character) for character in word)


def _number(text, label, lengths):
    match = re.search(_label(label) + r"\s*[:：]\s*([0-9]+)(?![0-9])", text)
    if match and len(match[1]) in lengths:
        return match[1]
    return None


def _amount(text):
    anchor = re.search(r"(?:\(\s*" + _label("小写") + r"\s*\)|" + _label("小写") + r")\s*[:：]?", text)
    if anchor:
        tail = text[anchor.end():]
    else:
        total = re.search(_label("价税合计") + r"[^\n]*?((?:[+-]\s*)?[¥￥])", text)
        if not total:
            return None
        tail = text[total.start(1):]
    match = re.match(r"\s*([+-]?\s*[¥￥]?\s*[+-]?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?)(?![0-9.,])", tail)
    if not match:
        return None
    token = re.sub(r"[\s¥￥]", "", match[1])
    if not re.fullmatch(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?", token):
        return None
    try:
        return format(Decimal(token.replace(",", "")).quantize(Decimal("0.01")), "f")
    except InvalidOperation:
        return None


def _names(text):
    field_labels = "|".join(_label(word) for word in (
            "名称", "纳税人识别号", "统一社会信用代码", "地址", "电话", "开户行", "账号", "购买方", "销售方"
        ))
    stop = re.compile(
        r"\s*(?:" + field_labels + r")\s*[:：]|\s*(?:" +
        _label("购买方") + "|" + _label("销售方") + r")\s*(?=" + _label("名称") + r"\s*[:：])"
    )
    roles = list(re.finditer(_label("购买方") + "|" + _label("销售方"), text))
    # A lookahead also finds a second name on the same extracted PDF row.
    names = []
    for match in re.finditer(r"(?=" + _label("名称") + r"\s*[:：]\s*([^\n]+))", text):
        value = re.split(stop, match[1], maxsplit=1)[0].strip()
        if value:
            preceding = [role for role in roles if role.end() <= match.start()]
            role = re.sub(r"\s", "", preceding[-1][0]) if preceding else None
            names.append((role, value))
    result = {"buyer": None, "seller": None}
    for role, value in names:
        if role:
            result["buyer" if role == "购买方" else "seller"] = value
    # Legacy vertically arranged invoices often have no readable section label.
    if len(names) >= 2:
        result["buyer"] = result["buyer"] or names[0][1]
        result["seller"] = result["seller"] or names[1][1]
    elif len(names) == 1 and names[0][0] is None:
        result["seller"] = names[0][1]
    return result


def read_invoice_data(pdf_path):
    pdf_path = Path(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        if BUNDLE_MARKER in (pdf.metadata.get("Keywords") or ""):
            raise MergedDocumentError("跳过合并结果")
        if not pdf.pages:
            raise InvoiceParseError("PDF 没有页面")
        text = pdf.pages[0].extract_text()
    if not text:
        raise InvoiceParseError("无法提取文本，可能是扫描件")
    text = unicodedata.normalize("NFKC", text).replace("−", "-")
    data = {key: None for key in INVOICE_FIELDS}
    data["number"] = _number(text, "发票号码", {8, 20})
    data["code"] = _number(text, "发票代码", {10, 12})
    if not data["number"]:
        raise InvoiceParseError("没有识别到有效发票号码，保留原文件名")
    date_pattern = r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    labelled = re.search(_label("开票日期") + r"\s*[:：]?\s*" + date_pattern, text)
    dates = [labelled] if labelled else re.finditer(date_pattern, text)
    for match in dates:
        try:
            data["date"] = date(*map(int, match.groups())).strftime("%Y%m%d")
            break
        except ValueError:
            continue
    data["amount"] = _amount(text)
    data.update(_names(text))
    return data


def extract_invoice_data(pdf_path):
    """Compatibility API: return None on unreadable/non-invoice documents."""
    try:
        return read_invoice_data(pdf_path)
    except Exception as exc:
        print(f"[提取失败] {Path(pdf_path).name}: {exc}")
        return None


def format_invoice_name(data, naming_format):
    fields = set()
    for _, field, spec, conversion in string.Formatter().parse(naming_format):
        if field is None:
            continue
        if field not in INVOICE_FIELDS or spec or conversion:
            raise ValueError(f"不支持的命名字段: {field}")
        fields.add(field)
    if not fields:
        raise ValueError("命名格式至少需要一个发票字段")
    missing = sorted(field for field in fields if data.get(field) is None or data.get(field) == "")
    if missing:
        raise InvoiceParseError("未识别到命名所需字段: " + ", ".join(missing))
    return clean_filename(naming_format.format(**data))


def choose_rename_path(source, basename):
    """Keep an already correct suffixed name even if an earlier slot is free."""
    source = Path(source)
    if re.fullmatch(re.escape(basename) + r"(?:_[1-9][0-9]*)?", source.stem, re.I):
        return source
    candidate = source.with_name(basename + ".pdf")
    counter = 1
    while candidate.exists():
        candidate = source.with_name(f"{basename}_{counter}.pdf")
        counter += 1
    return candidate


def rename_invoices(folder, naming_format):
    results = []
    for source in list_pdf_files(folder):
        if is_bundle_name(source):
            results.append(RenameResult(source, "skipped", reason="跳过合并结果"))
            continue
        try:
            data = read_invoice_data(source)
            if not data:
                raise InvoiceParseError("无法识别发票")
            target = choose_rename_path(source, format_invoice_name(data, naming_format))
            if source == target:
                results.append(RenameResult(source, "skipped", target, "无需重命名"))
                continue
            source.rename(target)
            results.append(RenameResult(source, "renamed", target))
        except MergedDocumentError as exc:
            results.append(RenameResult(source, "skipped", reason=str(exc)))
        except Exception as exc:
            results.append(RenameResult(source, "failed", reason=str(exc)))
    return results


def print_rename_results(results):
    for result in results:
        if result.status == "renamed":
            print(f"✅ 重命名: {result.source.name} -> {result.destination.name}")
        elif result.status == "failed":
            print(f"❌ 保留原名: {result.source.name}: {result.reason}")
        else:
            print(f"跳过: {result.source.name}: {result.reason}")
    counts = {status: sum(r.status == status for r in results) for status in ("renamed", "failed", "skipped")}
    print(f"处理完成！成功: {counts['renamed']}, 失败: {counts['failed']}, 跳过: {counts['skipped']}")
