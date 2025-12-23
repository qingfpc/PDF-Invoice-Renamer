import os
import re
import sys
import time
import pdfplumber
from pathlib import Path

# ================= 预设格式配置 =================
# 你可以在这里随意添加更多格式
PRESET_FORMATS = {
    "1": {
        "desc": "日期_销售方_金额 (例: 20231225_京东世纪贸易_299.00.pdf)",
        "fmt": "{date}_{seller}_{amount}"
    },
    "2": {
        "desc": "销售方_日期_金额 (例: 京东世纪贸易_20231225_299.00.pdf)",
        "fmt": "{seller}_{date}_{amount}"
    },
    "3": {
        "desc": "发票代码_发票号码 (例: 033001234567_12345678.pdf)",
        "fmt": "{code}_{number}"
    },
    "4": {
        "desc": "金额_销售方 (例: 299.00_京东世纪贸易.pdf)",
        "fmt": "{amount}_{seller}"
    }
}


# ===============================================

def clean_filename(filename):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()


def extract_invoice_data(pdf_path):
    """核心提取逻辑"""
    data = {
        'code': '未知代码', 'number': '未知号码',
        'date': '未知日期', 'amount': '0.00',
        'seller': '未知销售方', 'buyer': '未知购买方'
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            if not text: return None

            # 1. 提取发票代码
            code_match = re.search(r'发票代码[:：]\s*(\d+)', text)
            if code_match: data['code'] = code_match.group(1)

            # 2. 提取发票号码
            number_match = re.search(r'发票号码[:：]\s*(\d+)', text)
            if number_match: data['number'] = number_match.group(1)

            # 3. 提取日期
            date_match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
            if date_match:
                year, month, day = date_match.groups()
                data['date'] = f"{year}{month.zfill(2)}{day.zfill(2)}"

            # 4. 提取金额
            amount_match = re.search(r'\(小写\)[:：]?\s*[¥￥]?\s*([\d\.]+)', text)
            if not amount_match:
                amount_match = re.search(r'价税合计.*?[¥￥]\s*([\d\.]+)', text, re.DOTALL)
            if amount_match: data['amount'] = amount_match.group(1)

            # 5. 提取销售方 (简单启发式：取文中第二个出现的“名称：xxx”)
            names = re.findall(r'名称[:：]\s*([\u4e00-\u9fa5A-Za-z0-9\(\)（）]+)', text)
            if len(names) >= 2:
                data['seller'] = names[1]  # 通常第二个是销售方
            elif len(names) == 1:
                data['seller'] = names[0]

    except Exception as e:
        print(f"[ERROR] 读取文件出错: {e}")
        return None

    return data


def main():
    print("========================================")
    print("      PDF电子发票自动重命名工具 v1.0")
    print("========================================")

    # 1. 获取路径
    while True:
        target_dir_str = input("\n请输入发票所在的文件夹路径 (支持直接拖入文件夹): ").strip()
        # 去除两端的引号（Windows拖拽文件会自动加引号）
        target_dir_str = target_dir_str.strip('"').strip("'")

        target_path = Path(target_dir_str)
        if target_path.exists() and target_path.is_dir():
            break
        else:
            print("❌ 路径不存在或不是文件夹，请重新输入。")

    # 2. 选择格式
    print("\n请选择重命名格式：")
    for key, val in PRESET_FORMATS.items():
        print(f"  [{key}] {val['desc']}")

    fmt_choice = "1"
    while True:
        choice = input("\n请输入数字选择格式: ").strip()
        if choice in PRESET_FORMATS:
            fmt_choice = choice
            break
        print("❌ 输入无效，请输入列表中的数字。")

    selected_format = PRESET_FORMATS[fmt_choice]['fmt']
    print(f"\n已选择格式: {selected_format}")

    # 3. 确认执行
    input("\n>>> 按回车键 (Enter) 开始执行重命名...")

    # 4. 执行逻辑
    files = list(target_path.glob("*.pdf"))
    total = len(files)
    print(f"\n找到 {total} 个PDF文件，开始处理...\n")

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for idx, file_path in enumerate(files, 1):
        print(f"[{idx}/{total}] 正在读取: {file_path.name} ... ", end="")

        # 提取数据
        info = extract_invoice_data(file_path)

        if not info:
            print("❌ 无法识别内容 (可能是扫描件)")
            fail_count += 1
            continue

        # 生成新文件名
        new_name_base = selected_format.format(**info)
        new_name_base = clean_filename(new_name_base)
        new_name = f"{new_name_base}.pdf"
        new_path = target_path / new_name

        # 检查是否需要重命名
        if new_path == file_path:
            print("⚠️ 无需重命名")
            skipped_count += 1
            continue

        # 处理重名冲突
        if new_path.exists():
            counter = 1
            while new_path.exists():
                new_name = f"{new_name_base}_{counter}.pdf"
                new_path = target_path / new_name
                counter += 1

        try:
            file_path.rename(new_path)
            print(f"✅ 完成 -> {new_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            fail_count += 1

    # 5. 结束
    print("\n" + "=" * 40)
    print(f"处理完成！成功: {success_count}, 失败: {fail_count}, 跳过: {skipped_count}")
    print("=" * 40)
    input("\n按回车键退出程序...")


if __name__ == "__main__":
    main()