"""Standalone stamp-preserving, multi-page A4 invoice merger."""
from pathlib import Path

from invoice_core import clean_path
from invoice_merge import merge_pdf_files, print_merge_result, resolve_output_path


def get_clean_path(prompt_text):
    return clean_path(input(prompt_text))


def merge_invoices():
    print("发票 A4 排版合并工具（图片模式，保留可见印章）")
    while True:
        value = get_clean_path("请输入发票 PDF 所在文件夹: ")
        input_folder = Path(value)
        if value and input_folder.is_dir():
            break
        print("文件夹不存在，请重新输入。")
    while True:
        value = get_clean_path("请输入输出目录或 PDF 文件名 (回车 = 原文件夹): ")
        try:
            output = resolve_output_path(value, input_folder, "排版后发票合集.pdf")
            break
        except (ValueError, OSError) as exc:
            print(f"输出路径无效: {exc}")
    result = None
    try:
        result = merge_pdf_files(input_folder, output)
        print_merge_result(result)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"❌ 合并未完成: {exc}")
    input("按回车键退出...")
    return result


if __name__ == "__main__":
    try:
        merge_invoices()
    except (EOFError, KeyboardInterrupt):
        print("已取消。")
