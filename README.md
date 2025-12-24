# PDF Invoice Renamer (电子发票自动重命名工具)

这是一个基于 Python 开发的轻量级工具，旨在帮助财务人员、行政人员或开发者批量处理 PDF 电子发票。它能自动提取发票中的**关键信息**（如日期、销售方、金额、发票号等），并按照你指定的格式对文件进行重命名。

## ✨ 功能特点

* **自动提取**：利用 `pdfplumber` 提取 PDF 文本，识别发票代码、号码、日期、金额及销售方。
* **批量处理**：一键处理文件夹内所有 PDF 文件。
* **格式自定义**：支持多种重命名格式（如：`日期_销售方_金额` 或 `发票代码_发票号码`）。
* **智能防重**：如果重命名后的文件名已存在，自动添加序号避免覆盖。
* **开箱即用**：提供打包好的 `.exe` 程序，无需安装 Python 环境即可在 Windows 上运行。

---

## 🚀 快速开始 (针对普通用户)

如果你不懂编程，只想快速使用本工具，请按照以下步骤操作：

1.  **下载程序**：
    * 进入本仓库的 [Releases 页面](https://github.com/qingfpc/PDF-Invoice-Renamer/releases/latest) 下载最新 Release。
    * 下载 `InvoiceRenamer.exe` 文件。

2.  **运行工具**：
    * 双击打开 `InvoiceRenamer.exe`。
    * 按照提示输入（或拖入）存放发票的文件夹路径。
    * 输入数字选择你喜欢的重命名格式（例如输入 `1` 选择 `日期_销售方_金额`）。
    * 按回车键，等待处理完成。

3.  **查看结果**：
    * 处理完成后，文件夹内的 PDF 文件将自动变为规范的文件名。

---

## 💻 开发指南 (针对开发者)

如果你想查看源码或进行二次开发，请参考以下说明。

### 📂 项目结构

* `invoice_tool.py`: **主程序入口**。包含交互式命令行逻辑（CLI），用于打包 exe。
* `rename_invoices.py`: **核心逻辑类**。包含 `InvoiceRenamer` 类，封装了 PDF 解析和重命名逻辑，适合模块化调用。
* `dist/`: 存放编译好的可执行文件。

### 🔧 环境依赖

本项目使用 Python 3.14 开发。

1.  克隆仓库：
    ```bash
    git clone [https://github.com/你的用户名/invoice-renamer.git](https://github.com/你的用户名/invoice-renamer.git)
    cd invoice-renamer
    ```

2.  安装依赖库：
    ```bash
    pip install pdfplumber
    ```

3.  运行脚本：
    ```bash
    python invoice_tool.py
    ```

### 📦 如何打包成 EXE

如果你修改了代码并想重新打包：

1.  安装 PyInstaller：
    ```bash
    pip install pyinstaller
    ```

2.  执行打包命令：
    ```bash
    pyinstaller --onefile --name InvoiceRenamer invoice_tool.py
    ```

---

###  exe界面展示：
<img width="1113" height="626" alt="fdff57eb-f116-4eb7-9026-ff6aeba45b05" src="https://github.com/user-attachments/assets/b84eb61e-b146-4a87-9d53-ea110903503e" />

<img width="1113" height="626" alt="50ca0117-9d4f-4b6b-8f82-450064410036" src="https://github.com/user-attachments/assets/6235d18b-c014-4849-a9a4-20e08603da79" />

<img width="1113" height="626" alt="49ac645c-25cd-440c-bd93-1af7a18f987e" src="https://github.com/user-attachments/assets/decb9372-3d26-4f9e-8412-608796a9964d" />


## 📝 支持的重命名格式

工具内置了以下几种常用格式，你也可以在 `invoice_tool.py` 的 `PRESET_FORMATS` 字典中轻松添加新格式：

* **格式 1**: `{date}_{seller}_{amount}` (例: `20231225_京东世纪贸易_299.00.pdf`)
* **格式 2**: `{seller}_{date}_{amount}` (例: `京东世纪贸易_20231225_299.00.pdf`)
* **格式 3**: `{code}_{number}` (例: `033001234567_12345678.pdf`)
* **格式 4**: `{amount}_{seller}` (例: `299.00_京东世纪贸易.pdf`)

## ⚠️ 局限性与已知问题

* **仅支持标准电子发票**：目前主要针对中国增值税电子普通/专用发票。对于非标准的行程单、定额发票可能无法精确提取。
* **不支持纯图片扫描件**：如果 PDF 是由图片直接转换而来（无法选中文字），本工具无法提取信息。需要 OCR 技术的支持（未来版本计划加入）。

## 📄 License

MIT License
