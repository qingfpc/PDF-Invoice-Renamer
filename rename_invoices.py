import os
import re
import pdfplumber
from pathlib import Path

# ================= 配置区域 =================
# 目标文件夹路径 (可以是绝对路径，也可以是相对于脚本的路径)
# 修改为你存放发票的实际路径
# TARGET_FOLDER = './invoices'
TARGET_FOLDER = 'G:\发票\发票副本'

# 重命名格式模板
# 可用变量: {date}, {code}, {number}, {amount}, {seller}, {buyer}
# 例如: "{date}_{seller}_{amount}" 或 "发票-{code}-{number}"
# {date}: 开票日期 (如 20231201)
# {amount}: 金额 (如 100.00)
# {seller}: 销售方名称 (如 某某科技公司)
# {buyer}: 购买方名称
# {code}: 发票代码
# {number}: 发票号码
NAMING_FORMAT = "{date}_{seller}_{amount}"

# 如果解析失败，文件名前加的前缀
UNKNOWN_PREFIX = "解析失败_"


# ===========================================

class InvoiceRenamer:
    def __init__(self, folder_path, naming_format):
        self.folder_path = Path(folder_path)
        self.naming_format = naming_format

    def clean_text(self, text):
        """简单的文本清洗，去除多余空格"""
        if text:
            return text.replace(" ", "").replace(" ", "")  # 去除普通空格和不换行空格
        return ""

    def extract_invoice_data(self, pdf_path):
        """
        从PDF中提取关键信息。
        针对标准中国电子发票布局进行了优化。
        """
        data = {
            'code': '未知代码',
            'number': '未知号码',
            'date': '未知日期',
            'amount': '0.00',
            'seller': '未知销售方',
            'buyer': '未知购买方'
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 只读取第一页，通常发票只有一页
                page = pdf.pages[0]
                text = page.extract_text()

                if not text:
                    return None

                # 1. 提取发票代码 (10或12位数字)
                # 匹配：发票代码: 123456789012
                code_match = re.search(r'发票代码[:：]\s*(\d+)', text)
                if code_match:
                    data['code'] = code_match.group(1)

                # 2. 提取发票号码 (8位或20位数字)
                number_match = re.search(r'发票号码[:：]\s*(\d+)', text)
                if number_match:
                    data['number'] = number_match.group(1)

                # 3. 提取日期 (格式：2023年05月21日 -> 20230521)
                date_match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
                if date_match:
                    year, month, day = date_match.groups()
                    data['date'] = f"{year}{month.zfill(2)}{day.zfill(2)}"

                # 4. 提取金额 (小写)
                # 通常位于 "小写" 或 "¥" 符号后
                amount_match = re.search(r'\(小写\)[:：]?\s*[¥￥]?\s*([\d\.]+)', text)
                if not amount_match:
                    # 备选方案：找价税合计相关
                    amount_match = re.search(r'价税合计.*?[¥￥]\s*([\d\.]+)', text, re.DOTALL)

                if amount_match:
                    data['amount'] = amount_match.group(1)

                # 5. 提取销售方名称
                # 这是一个难点，因为名称格式不固定。通常在 "称：" 或 "称:" 后面，且在 "销售" 区域
                # 这里使用简单的启发式：查找“名称”且位置靠后的通常是销售方（但这不绝对），
                # 或者直接查找“销售方”区块下的名称。
                # 为了简化，我们尝试匹配“名称”后的一段文字，通常发票上有两个“名称”，第一个是购买方，第二个是销售方。
                names = re.findall(r'名称[:：]\s*([\u4e00-\u9fa5A-Za-z0-9\(\)（）]+)', text)
                if len(names) >= 2:
                    data['buyer'] = names[0]  # 第一个通常是购买方
                    data['seller'] = names[1]  # 第二个通常是销售方
                elif len(names) == 1:
                    data['seller'] = names[0]  # 只有一个的时候假设是销售方

        except Exception as e:
            print(f"读取PDF出错 {pdf_path.name}: {e}")
            return None

        return data

    def rename(self):
        if not self.folder_path.exists():
            print(f"错误: 文件夹 '{self.folder_path}' 不存在。")
            return

        print(f"正在扫描文件夹: {self.folder_path} ...")

        files = list(self.folder_path.glob("*.pdf"))
        if not files:
            print("未找到PDF文件。")
            return

        for file_path in files:
            # 这里的 .stem 是文件名(不含后缀)
            if UNKNOWN_PREFIX in file_path.stem:
                continue  # 跳过已经标记失败的文件

            print(f"正在处理: {file_path.name}")
            info = self.extract_invoice_data(file_path)

            if info:
                # 生成新文件名
                new_name_str = self.naming_format.format(**info) + ".pdf"

                # 处理文件名中可能包含的非法字符 (如斜杠)
                new_name_str = re.sub(r'[\\/*?:"<>|]', "", new_name_str)

                new_path = self.folder_path / new_name_str

                # 防止重名覆盖 (如果文件已存在，添加序号)
                if new_path.exists() and new_path != file_path:
                    counter = 1
                    while new_path.exists():
                        new_name_str = f"{self.naming_format.format(**info)}_{counter}.pdf"
                        new_path = self.folder_path / new_name_str
                        counter += 1

                try:
                    file_path.rename(new_path)
                    print(f" -> 重命名为: {new_path.name}")
                except OSError as e:
                    print(f" -> 重命名失败: {e}")
            else:
                print(f" -> 无法提取文本 (可能是图片扫描件?)")
                # 可选：重命名为 "解析失败_原文件名.pdf"
                # fail_path = self.folder_path / (UNKNOWN_PREFIX + file_path.name)
                # file_path.rename(fail_path)


if __name__ == "__main__":
    # 确保有一个测试文件夹
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"已创建测试文件夹 '{TARGET_FOLDER}'，请放入PDF发票文件后再次运行。")
    else:
        renamer = InvoiceRenamer(TARGET_FOLDER, NAMING_FORMAT)
        renamer.rename()