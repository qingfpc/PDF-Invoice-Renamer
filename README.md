[English](README.en.md) | [简体中文](README.md)

# PDF Invoice Helper (电子发票助手：重命名 + A4合并)

这是一个基于 Python 开发的轻量级办公自动化工具，旨在帮助财务人员、行政人员或开发者批量处理 PDF 电子发票。

它不仅能自动提取发票中的**关键信息**（如日期、销售方、金额、发票号等）进行重命名，还能将多张发票**智能排版合并**到一个 PDF 文件中（A4 纸上下两张），极大地简化了报销打印流程。

## ✨ 功能特点

### 1. 智能重命名
* **自动提取**：利用 `pdfplumber` 提取 PDF 文本，精确识别发票代码、号码、日期、金额及销售方。
* **格式自定义**：支持多种重命名格式（如：`日期_销售方_金额` 或 `发票代码_发票号码`）。
* **智能防重**：如果重命名后的文件名已存在，自动添加序号避免覆盖。

### 2. A4 自动排版合并
* **智能拼版**：将两张发票上下排列放置在一张 A4 页面上（2合1），节省纸张。
* **单张处理**：如果是奇数张发票，最后一张自动占据上半页。
* **自定义输出**：支持将合并后的文件导出到指定目录。

### 3. 便捷易用
* **批量处理**：一键处理文件夹内所有 PDF 文件。
* **开箱即用**：提供打包好的 `.exe` 程序，无需安装 Python 环境即可在 Windows 上运行。

---

## 🚀 快速开始 (针对普通用户)

如果你不懂编程，只想快速使用本工具，请按照以下步骤操作：

1.  **下载程序**：
    * 进入本仓库的 [Releases 页面](https://github.com/qingfpc/PDF-Invoice-Renamer/releases/latest) 下载最新 Release。
    * 根据需求下载对应的工具：
        * `InvoiceHelper_AllInOne.exe`：**全功能助手**，支持自动重命名并合并排版（推荐）。
        * `InvoiceRenamer_Only.exe`：**重命名工具**，仅执行发票信息提取与重命名。
        * `InvoiceMerger_Only.exe`：**排版工具**，仅执行发票 A4 拼版与 PDF 合并。

2. **运行工具**：
    * 双击打开对应的 `.exe` 文件。
    * 按照屏幕提示输入（或直接拖入）存放发票的文件夹路径，并选择对应选项即可。

---

## 💻 开发指南 (针对开发者)

如果你想查看源码或进行二次开发，请参考以下说明。

### 📂 项目结构

* `invoiceMaster.py`: **[推荐] 全功能主程序**。整合了重命名与合并功能，提供完整的交互式 CLI。
* `mergeInvoices.py`: **独立合并脚本**。仅包含 A4 排版合并逻辑。
* `renameInvoices.py`: **核心重命名逻辑**。封装了 PDF 解析类，适合模块化调用。
* `invoiceTool.py`: (旧版) 仅包含重命名功能的入口脚本。

### 🔧 环境依赖

本项目使用 Python 3.x 开发。

1.  克隆仓库：
    ```bash
    git clone [https://github.com/qingfpc/PDF-Invoice-Renamer.git](https://github.com/qingfpc/PDF-Invoice-Renamer.git)
    ```

2.  安装依赖库 (新增 pymupdf 用于处理合并)：
    ```bash
    pip install pdfplumber pymupdf
    ```

3.  运行脚本：
    ```bash
    python invoice_master.py
    ```

### 📦 如何打包成 EXE

如果你修改了代码并想重新打包，请使用 `PyInstaller`：

1.  安装 PyInstaller：
    ```bash
    pip install pyinstaller
    ```

2.  执行打包命令 (打包主程序)：
    ```bash
    pyinstaller --onefile --name InvoiceHelper invoice_master.py
    ```

---

## 🖼️ 界面展示
<img width="1113" height="626" alt="fdff57eb-f116-4eb7-9026-ff6aeba45b05" src="https://github.com/user-attachments/assets/b84eb61e-b146-4a87-9d53-ea110903503e" />

<img width="1113" height="626" alt="50ca0117-9d4f-4b6b-8f82-450064410036" src="https://github.com/user-attachments/assets/6235d18b-c014-4849-a9a4-20e08603da79" />

<img width="1113" height="626" alt="49ac645c-25cd-440c-bd93-1af7a18f987e" src="https://github.com/user-attachments/assets/decb9372-3d26-4f9e-8412-608796a9964d" />


## 📝 支持的重命名格式

工具内置了以下几种常用格式，你也可以在代码的 `PRESET_FORMATS` 字典中轻松添加新格式：

* **格式 1**: `{date}_{seller}_{amount}` (例: `20231225_京东世纪贸易_299.00.pdf`)
* **格式 2**: `{seller}_{date}_{amount}` (例: `京东世纪贸易_20231225_299.00.pdf`)
* **格式 3**: `{code}_{number}` (例: `033001234567_12345678.pdf`)
* **格式 4**: `{amount}_{seller}` (例: `299.00_京东世纪贸易.pdf`)

## ⚠️ 局限性与已知问题

* **仅支持标准电子发票**：目前主要针对中国增值税电子普通/专用发票。对于非标准的行程单、定额发票可能无法精确提取。
* **不支持纯图片扫描件**：如果 PDF 是由图片直接转换而来（无法选中文字），本工具无法提取信息。需要 OCR 技术的支持。

## 📄 License

MIT License