"""Standalone interactive invoice renamer."""
from pathlib import Path

from invoice_core import (PRESET_FORMATS, clean_filename, clean_path,
                          extract_invoice_data, print_rename_results, rename_invoices)


def main():
    print("PDF电子发票自动重命名工具")
    while True:
        value = clean_path(input("请输入发票所在的文件夹路径 (支持拖入文件夹): "))
        target_path = Path(value)
        if value and target_path.is_dir():
            break
        print("路径不存在或不是文件夹，请重新输入。")
    for key, preset in PRESET_FORMATS.items():
        print(f"  [{key}] {preset['desc']}")
    while True:
        choice = input("请输入数字选择格式 (默认1): ").strip() or "1"
        if choice in PRESET_FORMATS:
            break
        print("输入无效，请输入列表中的数字。")
    input("按回车键开始执行重命名...")
    results = rename_invoices(target_path, PRESET_FORMATS[choice]["fmt"])
    print_rename_results(results)
    input("按回车键退出程序...")
    return results


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("已取消。")
