"""Stamp-preserving A4 layout shared by both merging entry points."""

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz

from invoice_core import BUNDLE_MARKER, is_bundle_name, list_pdf_files

A4_WIDTH = 595
A4_HEIGHT = 842


@dataclass
class MergeFailure:
    source: Path
    reason: str
    page_number: Optional[int] = None


@dataclass
class MergeResult:
    output: Optional[Path] = None
    input_files: int = 0
    input_pages: int = 0
    merged_pages: int = 0
    output_pages: int = 0
    failures: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def resolve_output_path(value, input_folder, default_name):
    """Accept a directory or a complete PDF filename, preserving existing files."""
    destination = Path(value) if value else Path(input_folder)
    if not destination.is_dir() and destination.suffix.lower() == ".pdf":
        output = destination
    else:
        output = destination / default_name
    if output.parent.exists() and not output.parent.is_dir():
        raise ValueError("输出文件的上级路径不是文件夹")
    counter = 1
    candidate = output
    while candidate.exists():
        candidate = output.with_name(f"{output.stem}_{counter}{output.suffix}")
        counter += 1
    return candidate


def merge_pdf_files(input_folder, output_path):
    input_folder, output_path = Path(input_folder), Path(output_path)
    result = MergeResult()
    files = list_pdf_files(input_folder)
    output_resolved = output_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"输出文件已存在，拒绝覆盖: {output_path}")
    matrix = fitz.Matrix(3.0, 3.0)
    with fitz.open() as output:
        for source in files:
            if source.resolve() == output_resolved or is_bundle_name(source):
                result.skipped.append(source)
                continue
            result.input_files += 1
            try:
                with fitz.open(source) as document:
                    if not document.is_pdf:
                        raise ValueError("文件内容不是 PDF")
                    if document.needs_pass:
                        raise ValueError("PDF 已加密，需要先解密")
                    if BUNDLE_MARKER in ((document.metadata or {}).get("keywords") or ""):
                        result.skipped.append(source)
                        result.input_files -= 1
                        continue
                    if not document.page_count:
                        raise ValueError("PDF 没有页面")
                    result.input_pages += document.page_count
                    for index in range(document.page_count):
                        created_sheet = False
                        try:
                            # Render before allocating a slot, so failures do not
                            # create empty half-pages. Annotations remain visible.
                            pixmap = document[index].get_pixmap(matrix=matrix, alpha=False, annots=True)
                            new_sheet = result.merged_pages % 2 == 0
                            page = output.new_page(width=A4_WIDTH, height=A4_HEIGHT) if new_sheet else output[-1]
                            created_sheet = new_sheet
                            top = 10 if new_sheet else A4_HEIGHT / 2 + 10
                            bottom = A4_HEIGHT / 2 - 10 if new_sheet else A4_HEIGHT - 10
                            page.insert_image(fitz.Rect(10, top, A4_WIDTH - 10, bottom),
                                              pixmap=pixmap, keep_proportion=True)
                            result.merged_pages += 1
                        except Exception as exc:
                            if created_sheet:
                                output.delete_page(-1)
                            result.failures.append(MergeFailure(source, str(exc), index + 1))
            except Exception as exc:
                result.failures.append(MergeFailure(source, str(exc)))
        if not result.merged_pages:
            return result
        output.set_metadata({"producer": "PDF Invoice Helper", "keywords": BUNDLE_MARKER})
        result.output_pages = len(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Save completely before publishing; close every source before renaming.
        with tempfile.NamedTemporaryFile(prefix=".invoice-", suffix=".tmp", dir=output_path.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            output.save(temporary_path, deflate=True)
            with fitz.open(temporary_path) as check:
                if len(check) != result.output_pages:
                    raise ValueError("输出 PDF 页数校验失败")
            if output_path.exists():
                raise FileExistsError(f"输出文件已存在，拒绝覆盖: {output_path}")
            temporary_path.rename(output_path)
            result.output = output_path
        finally:
            temporary_path.unlink(missing_ok=True)
    return result


def print_merge_result(result):
    for failure in result.failures:
        page = f" 第 {failure.page_number} 页" if failure.page_number else ""
        print(f"❌ 处理失败: {failure.source.name}{page}: {failure.reason}")
    if result.output is None:
        print("未生成合并文件：没有可合并的页面。")
    else:
        status = "⚠️ 部分完成，存在遗漏，请检查失败列表" if result.failures else "✅ 合并成功"
        print(f"{status}：合并 {result.merged_pages} 个源页面，输出 {result.output_pages} 张 A4。")
        print(f"文件已保存至: {result.output}")
    print(f"失败项: {len(result.failures)}, 跳过已有合集: {len(result.skipped)}")
