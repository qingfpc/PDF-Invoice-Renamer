import time
from pathlib import Path

from invoice_core import (PRESET_FORMATS, clean_filename, clean_path,
                          extract_invoice_data, print_rename_results, rename_invoices)

from invoice_merge import (A4_WIDTH, A4_HEIGHT, merge_pdf_files,
                           print_merge_result, resolve_output_path)


def clean_path_input(prompt_text):
    """Remove enclosing quotes without altering the actual path."""
    return clean_path(input(prompt_text))


def run_renamer(target_path):
    print("\n >>> 进入重命名模式")
    for key, value in PRESET_FORMATS.items():
        print(f"  [{key}] {value['desc']}")
    choice = input("请输入数字选择 (默认为1): ").strip()
    selected_format = PRESET_FORMATS.get(choice, PRESET_FORMATS["1"])["fmt"]
    results = rename_invoices(target_path, selected_format)
    if not results:
        print("该目录下没有PDF文件。")
    print_rename_results(results)
    return results


def run_merger(input_dir_path):
    print("\n >>> 进入 A4 图片合并模式（保留可见印章，文字转为图片）")
    value = clean_path_input("请输入输出目录或 PDF 文件名 (回车 = 原文件夹): ")
    try:
        output = resolve_output_path(value, input_dir_path,
                                     f"发票合集_图片版_{int(time.time())}.pdf")
        result = merge_pdf_files(input_dir_path, output)
        print_merge_result(result)
        return result
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"❌ 合并未完成: {exc}")
        return None


def main():
    print("=" * 50)
    print("     发票助手: 智能重命名 + A4合并排版")
    print("=" * 50)

    # 1. 获取工作目录
    while True:
        target_dir_str = clean_path_input("\n请输入发票所在的文件夹路径: ")
        target_path = Path(target_dir_str)
        if target_dir_str and target_path.is_dir():
            break
        print("❌ 路径无效，请重新输入。")

    # 2. 询问是否重命名
    choice_rename = input("\n是否需要【自动重命名】发票? (y/n, 默认y): ").strip().lower()
    if choice_rename != 'n':
        run_renamer(target_path)
    else:
        print("已跳过重命名。")

    # 3. 询问是否合并
    choice_merge = input("\n是否需要将发票【合并】为一个PDF? (y/n, 默认y): ").strip().lower()
    if choice_merge != 'n':
        run_merger(target_path)
    else:
        print("已跳过合并。")

    print("\n" + "=" * 50)
    print("所有任务已结束。")
    input("按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("已取消。")
    except Exception as e:
        print(f"发生未知错误: {e}")
        input("按回车键退出...")