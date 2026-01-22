import os
import re
import sys
import time
import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path

# ================= 配置区域 =================
PRESET_FORMATS = {
    "1": {"desc": "日期_销售方_金额 (例: 20231225_京东_299.00.pdf)", "fmt": "{date}_{seller}_{amount}"},
    "2": {"desc": "销售方_日期_金额 (例: 京东_20231225_299.00.pdf)", "fmt": "{seller}_{date}_{amount}"},
    "3": {"desc": "发票代码_发票号码 (例: 0330012_12345678.pdf)", "fmt": "{code}_{number}"},
    "4": {"desc": "金额_销售方 (例: 299.00_京东.pdf)", "fmt": "{amount}_{seller}"}
}

# A4 尺寸 (点): 595 x 842
A4_WIDTH = 595
A4_HEIGHT = 842


def clean_path_input(prompt_text):
    """获取并清洗路径输入"""
    path_str = input(prompt_text).strip()
    return path_str.replace('"', '').replace("'", "")


def clean_filename(filename):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()


def extract_invoice_data(pdf_path):
    """使用 pdfplumber 提取发票关键信息"""
    data = {
        'code': '未知代码', 'number': '未知号码',
        'date': '未知日期', 'amount': '0.00',
        'seller': '未知销售方', 'buyer': '未知购买方'
    }
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages: return None
            page = pdf.pages[0]
            text = page.extract_text()
            if not text: return None

            # 1. 发票代码
            code_match = re.search(r'发票代码[:：]\s*(\d+)', text)
            if code_match: data['code'] = code_match.group(1)

            # 2. 发票号码
            number_match = re.search(r'发票号码[:：]\s*(\d+)', text)
            if number_match: data['number'] = number_match.group(1)

            # 3. 日期
            date_match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
            if date_match:
                year, month, day = date_match.groups()
                data['date'] = f"{year}{month.zfill(2)}{day.zfill(2)}"

            # 4. 金额
            amount_match = re.search(r'\(小写\)[:：]?\s*[¥￥]?\s*([\d\.]+)', text)
            if not amount_match:
                amount_match = re.search(r'价税合计.*?[¥￥]\s*([\d\.]+)', text, re.DOTALL)
            if amount_match: data['amount'] = amount_match.group(1)

            # 5. 销售方 (启发式：取第二个名称，或者唯一的名称)
            names = re.findall(r'名称[:：]\s*([\u4e00-\u9fa5A-Za-z0-9\(\)（）]+)', text)
            if len(names) >= 2:
                data['seller'] = names[1]
            elif len(names) == 1:
                data['seller'] = names[0]

    except Exception as e:
        print(f"  [提取失败] {pdf_path.name}: {e}")
        return None
    return data


def run_renamer(target_path):
    """执行重命名逻辑"""
    print("\n" + "-" * 40)
    print(" >>> 进入重命名模式")
    print("-" * 40)

    # 选择格式
    print("请选择重命名格式：")
    for key, val in PRESET_FORMATS.items():
        print(f"  [{key}] {val['desc']}")

    fmt_choice = input("请输入数字选择 (默认为1): ").strip()
    if fmt_choice not in PRESET_FORMATS: fmt_choice = "1"
    selected_format = PRESET_FORMATS[fmt_choice]['fmt']

    print(f"已选择格式: {selected_format}\n")

    files = list(target_path.glob("*.pdf"))
    if not files:
        print("该目录下没有PDF文件。")
        return

    success_count = 0
    for file_path in files:
        # 跳过看起来已经是合并过的文件
        if "发票合集" in file_path.name: continue

        info = extract_invoice_data(file_path)
        if not info: continue

        new_name_base = selected_format.format(**info)
        new_name_base = clean_filename(new_name_base)
        new_name = f"{new_name_base}.pdf"
        new_path = target_path / new_name

        if new_path == file_path: continue

        # 处理重名
        if new_path.exists():
            counter = 1
            while new_path.exists():
                new_name = f"{new_name_base}_{counter}.pdf"
                new_path = target_path / new_name
                counter += 1

        try:
            file_path.rename(new_path)
            print(f"✅ 重命名: {file_path.name} -> {new_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ 失败: {e}")

    print(f"\n重命名完成，共处理 {success_count} 个文件。")


def run_merger(input_dir_path):
    """
        执行合并逻辑。
        注意：为了兼容全电发票的特殊图层（防止印章丢失），
        这里放弃了纯矢量合并，改用高清位图渲染方案。
        """
    print("\n" + "-" * 40)
    print(" >>> 进入【截图式】强力合并模式")
    print("     (解决一切印章丢失问题，但文字将转为图片)")
    print("-" * 40)

    # 1. 确定输出目录
    out_input = clean_path_input("请输入输出目录 (直接回车 = 输出到原文件夹): ")
    output_dir = Path(out_input) if out_input else input_dir_path
    if not output_dir.exists(): output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = output_dir / f"发票合集_图片版_{int(time.time())}.pdf"

    # 2. 扫描文件
    pdf_files = sorted([f for f in input_dir_path.glob("*.pdf") if "发票合集" not in f.name])
    if not pdf_files:
        print("没有找到可合并的PDF文件。")
        return

    doc_out = fitz.open()

    # 设置渲染清晰度 (2.0 = 144 DPI, 3.0 = 216 DPI)
    # 3.0 对于打印足够清晰，且文件体积可控
    ZOOM_MATRIX = fitz.Matrix(3.0, 3.0)

    for i in range(0, len(pdf_files), 2):
        # 创建A4空白页
        page = doc_out.new_page(width=A4_WIDTH, height=A4_HEIGHT)

        def paste_invoice_as_image(file_path, target_rect):
            try:
                src_doc = fitz.open(file_path)
                src_page = src_doc[0]

                # --- 核心修改：渲染为图片 (Rasterization) ---
                # 这会将当前页面看到的所有内容（含印章）转换成像素数据
                pix = src_page.get_pixmap(matrix=ZOOM_MATRIX, alpha=False)

                # 将图片插入到目标 PDF 页面
                # keep_proportion=True 保证发票不会变形
                page.insert_image(
                    target_rect,
                    pixmap=pix,
                    keep_proportion=True
                )
                src_doc.close()
            except Exception as e:
                print(f"  处理 {file_path.name} 失败: {e}")

        # --- 上半部分 ---
        file1 = pdf_files[i]
        print(f"排版: [上] {file1.name}")
        # 定义上半部分区域 (留一点边距美观)
        rect_top = fitz.Rect(10, 10, A4_WIDTH - 10, A4_HEIGHT / 2 - 10)
        paste_invoice_as_image(file1, rect_top)

        # --- 下半部分 ---
        if i + 1 < len(pdf_files):
            file2 = pdf_files[i + 1]
            print(f"排版: [下] {file2.name}")
            # 定义下半部分区域
            rect_bottom = fitz.Rect(10, A4_HEIGHT / 2 + 10, A4_WIDTH - 10, A4_HEIGHT - 10)
            paste_invoice_as_image(file2, rect_bottom)
        else:
            print("排版: [下] 空白")

    try:
        # 保存文件
        # deflate=True 压缩图片数据，减小体积
        doc_out.save(output_filename, deflate=True)
        print(f"\n✅ 合并成功！(图片模式)\n文件已保存至: {output_filename}")
    except Exception as e:
        print(f"\n❌ 保存PDF失败: {e}")
        print("请检查文件是否被占用。")
    finally:
        doc_out.close()


def main():
    print("=" * 50)
    print("     发票助手: 智能重命名 + A4合并排版")
    print("=" * 50)

    # 1. 获取工作目录
    while True:
        target_dir_str = clean_path_input("\n请输入发票所在的文件夹路径: ")
        target_path = Path(target_dir_str)
        if target_path.exists() and target_path.is_dir():
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
    except Exception as e:
        print(f"发生未知错误: {e}")
        input("按回车键退出...")