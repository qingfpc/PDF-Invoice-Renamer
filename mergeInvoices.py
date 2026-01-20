import os
import sys
import fitz  # PyMuPDF


def get_clean_path(prompt_text):
    """获取用户输入并清洗路径（去除引号）"""
    path = input(prompt_text).strip()
    # 去除Windows复制路径时可能带有的双引号
    return path.replace('"', '').replace("'", "")


def merge_invoices():
    print("=" * 50)
    print("      发票 A4 排版合并工具 (2合1)      ")
    print("=" * 50)

    # 1. 获取输入目录
    while True:
        input_dir = get_clean_path("请输入【发票PDF所在文件夹】路径: ")
        if os.path.isdir(input_dir):
            break
        print("错误：文件夹不存在，请重新输入。")

    # 2. 获取输出目录
    while True:
        output_dir = get_clean_path("请输入【合并后文件保存】位置: ")
        if os.path.isdir(output_dir):
            break
        # 如果用户输入的是想保存的文件名路径，尝试提取目录
        try:
            if os.path.isdir(os.path.dirname(output_dir)):
                break
        except:
            pass
        print("错误：输出路径无效，请确保文件夹存在。")

    output_filename = os.path.join(output_dir, "排版后发票合集.pdf")

    # 3. 收集PDF文件
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    pdf_files.sort()  # 按文件名排序

    if not pdf_files:
        print("错误：指定文件夹下没有找到PDF文件。")
        input("按回车键退出...")
        return

    print(f"\n找到 {len(pdf_files)} 个PDF文件，开始处理...\n")

    # 4. 创建输出文档 (A4尺寸)
    # A4 尺寸 (点): 595 x 842
    A4_WIDTH = 595
    A4_HEIGHT = 842
    doc_out = fitz.open()

    # 5. 循环处理
    for i in range(0, len(pdf_files), 2):
        # 创建一个新的A4页面
        page = doc_out.new_page(width=A4_WIDTH, height=A4_HEIGHT)

        # --- 处理第一张 (上半部分) ---
        file1 = pdf_files[i]
        path1 = os.path.join(input_dir, file1)
        print(f"正在排版 (上): {file1}")

        try:
            src1 = fitz.open(path1)
            # 定义上半部分的矩形区域 (x0, y0, x1, y1)
            # 上半部：从(0,0) 到 (宽, 高的一半)
            rect_top = fitz.Rect(0, 0, A4_WIDTH, A4_HEIGHT / 2)
            # show_pdf_page 会自动保持比例缩放并居中放置
            page.show_pdf_page(rect_top, src1, 0)  # 0 表示取源文件的第1页
            src1.close()
        except Exception as e:
            print(f"  -> 读取文件 {file1} 失败: {e}")

        # --- 处理第二张 (下半部分) - 如果存在 ---
        if i + 1 < len(pdf_files):
            file2 = pdf_files[i + 1]
            path2 = os.path.join(input_dir, file2)
            print(f"正在排版 (下): {file2}")

            try:
                src2 = fitz.open(path2)
                # 定义下半部分的矩形区域
                # 下半部：从(0, 高的一半) 到 (宽, 高)
                rect_bottom = fitz.Rect(0, A4_HEIGHT / 2, A4_WIDTH, A4_HEIGHT)
                page.show_pdf_page(rect_bottom, src2, 0)
                src2.close()
            except Exception as e:
                print(f"  -> 读取文件 {file2} 失败: {e}")
        else:
            print("(本页下半部分留空)")

    # 6. 保存文件
    try:
        doc_out.save(output_filename)
        print("\n" + "=" * 50)
        print(f"成功！文件已保存至:\n{output_filename}")
        print("=" * 50)
    except Exception as e:
        print(f"\n保存失败: {e}")
        print("请检查输出文件是否被打开，或者路径是否有写入权限。")

    doc_out.close()
    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        merge_invoices()
    except Exception as e:
        # 捕获所有未预料的错误，防止闪退
        print(f"发生未知错误: {e}")
        input("按回车键退出...")