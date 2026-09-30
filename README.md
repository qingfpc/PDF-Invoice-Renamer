[English](README.en.md) | [简体中文](README.md)

# PDF Invoice Helper：电子发票重命名与 A4 合并

批量读取 PDF 电子发票中的日期、金额、发票号码和购销双方名称，按所选格式重命名，再将 PDF 页面上下两张排版到 A4 纸上。你可以运行全功能程序，也可以分别使用重命名或合并工具。

本 README 描述当前 `main` 分支源码。已发布 EXE 的功能以对应 [Release 说明](https://github.com/qingfpc/PDF-Invoice-Renamer/releases)为准；使用当前源码的功能，请按下文构建程序。

## 功能与处理范围

处理时遵循以下规则：

- **重命名校验**：识别到有效发票号码后，再检查命名格式需要的字段。无法识别或缺少必要字段时保留原名，并报告原因
- **金额处理**：支持负数和千分位金额，命名时统一保留两位小数，例如 `1,234.56` 转为 `1234.56`
- **重复运行**：重名时添加序号，已符合格式的文件保留名称；已有输出文件不会被覆盖
- **A4 排版**：逐页处理每份 PDF，每张 A4 上下放置两个源页面；页面总数为奇数时，最后半页留白
- **印章与文字**：两个合并入口均以 216 DPI 渲染可见页面及注释。合并结果是图片，文字无法选中或搜索，适合打印；归档请保留原始发票
- **失败报告**：部分页面失败时输出成功页面，并列出遗漏；没有可合并页面时不生成空白结果

仅处理所选文件夹的当前层级，不扫描子文件夹，支持 `.pdf` 和 `.PDF`。重命名只读取第一页的发票信息；合并处理所有页面，并跳过本工具生成的已有合集。

**合并不判断 PDF 是否为发票。** 同一目录中未能重命名、但仍可读取的 PDF 也会参与合并。请将计划打印的文件放在单独的文件夹中。

## 使用 Windows EXE

从 [Releases 页面](https://github.com/qingfpc/PDF-Invoice-Renamer/releases/latest)选择对应版本的 EXE。下载的名称可能带版本后缀，例如 `InvoiceHelper_AllInOne_v2.0.1.exe`；下表列出当前源码构建的名称：

| 程序 | 功能 |
| --- | --- |
| `InvoiceHelper_AllInOne.exe` | 依次选择是否重命名、是否合并 |
| `InvoiceRenamer_Only.exe` | 仅提取发票信息并重命名 |
| `InvoiceMerger_Only.exe` | 仅合并 PDF 页面，支持扫描件 |

双击程序，按提示输入或拖入文件夹路径。合并时可输入输出目录或完整 PDF 文件名；直接回车表示输出到输入目录。不存在的输出目录会自动创建，重名输出自动追加序号。

## 从源码运行

已在 Windows 11、64 位 Python 3.12 上验证。下面的 `python` 命令需要指向 Python 3.12，先用 `python --version` 检查；如使用其他安装或 Conda 环境，请改用对应解释器。

克隆仓库，创建项目环境并安装运行依赖：

```powershell
git clone https://github.com/qingfpc/PDF-Invoice-Renamer.git
cd PDF-Invoice-Renamer
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

从仓库根目录运行所需入口：

```powershell
.\.venv\Scripts\python.exe invoiceMaster.py
```

独立工具分别使用以下命令：

```powershell
.\.venv\Scripts\python.exe invoiceTool.py
.\.venv\Scripts\python.exe mergeInvoices.py
```

## 选择重命名格式

交互入口提供四种格式。共享预设位于 [invoice_core.py](invoice_core.py) 的 `PRESET_FORMATS` 中：

| 选项 | 格式 | 文件名示例 |
| --- | --- | --- |
| 1 | `{date}_{seller}_{amount}` | `20231225_京东世纪贸易_299.00.pdf` |
| 2 | `{seller}_{date}_{amount}` | `京东世纪贸易_20231225_299.00.pdf` |
| 3 | `{code}_{number}` | `033001234567_12345678.pdf` |
| 4 | `{amount}_{seller}` | `299.00_京东世纪贸易.pdf` |

自定义格式可以使用以下字段：

| 字段 | 含义 |
| --- | --- |
| `{date}` | 开票日期，格式为 `YYYYMMDD` |
| `{seller}` | 销售方名称 |
| `{buyer}` | 购买方名称 |
| `{amount}` | 两位小数的金额，可为负数 |
| `{code}` | 10 位或 12 位发票代码 |
| `{number}` | 8 位或 20 位发票号码 |

使用命令行传入目录和自定义格式，例如按发票号码和金额命名：

```powershell
.\.venv\Scripts\python.exe renameInvoices.py "D:\发票" `
    --format "{number}_{amount}"
```

全电发票没有发票代码时，选项 3 会保留原名并报告缺少 `code`。请选择其他字段齐全的格式，或用上面的命令改为 `{number}`。

## 运行测试

从仓库根目录安装开发依赖，再执行测试；仅安装 `requirements.txt` 不包含测试使用的 PDF 生成库：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试生成临时 PDF，实际执行解析、重命名、渲染、合并和命令行进程，不修改个人发票。覆盖金额、字段缺失、文件冲突、重复运行、多页、旋转页、注释、扫描件、损坏及加密文件；生成样例不代表所有真实发票模板均已验证。

## 构建与验证 EXE

安装开发依赖后，使用 PowerShell 7 的 `pwsh` 从仓库根目录运行打包脚本：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pwsh -NoLogo -NoProfile -File .\build.ps1
```

脚本在 `dist/` 生成上表中的三个 EXE。`build/`、`dist/` 和 `.venv/` 均不提交到 Git；本地构建也不会自动更新 GitHub Release 附件。

构建完成后，复用交互流程测试验证三个 EXE：

```powershell
$env:INVOICE_TEST_EXE_DIR = (Join-Path (Get-Location) 'dist')
try {
    .\.venv\Scripts\python.exe -m unittest tests.test_cli -v
} finally {
    Remove-Item Env:\INVOICE_TEST_EXE_DIR -ErrorAction SilentlyContinue
}
```

## 模块与返回结果

代码按以下职责组织：

| 文件 | 职责 |
| --- | --- |
| `invoiceMaster.py` | 全功能交互入口 |
| `invoiceTool.py` | 独立重命名交互入口 |
| `mergeInvoices.py` | 独立合并交互入口 |
| `renameInvoices.py` | 可复用的 `InvoiceRenamer` 类及自定义格式命令行入口 |
| `invoice_core.py` | 共享解析、字段校验、路径清洗与重命名 |
| `invoice_merge.py` | 共享多页排版、输出保护与失败汇总 |
| `build.ps1` | 构建三个 Windows EXE |
| `tests/` | PDF 与命令行流程回归测试 |
| `requirements.txt` | 运行依赖 |
| `requirements-dev.txt` | 测试和打包依赖 |
| `constraints.txt` | 已验证的 Windows / Python 3.12 依赖版本 |

`extract_invoice_data()` 对不可识别文件返回 `None`；可识别发票中缺失的字段也是 `None`，不会返回“未知”占位符或伪造零金额。直接调用 `read_invoice_data()` 时，识别失败会抛出异常。调用方需先检查字段，再格式化文件名。

`rename_invoices()` 和 `InvoiceRenamer.rename()` 返回每个文件的结果，状态为 `renamed`、`skipped` 或 `failed`。`merge_pdf_files()` 返回源页面数、合并页面数、输出位置、失败项和跳过项；没有可用页面时 `output` 为 `None`。

## 已知限制

选择输入文件和处理结果时请注意以下限制：

- 重命名针对中国标准电子发票，要求识别到 8 位或 20 位发票号码；非标准票据可能无法识别
- 没有 OCR 功能，扫描件不能提取字段重命名，但可以合并打印
- 购销双方名称仍依赖标签和版式顺序推断，特殊模板需要核对识别结果
- 重命名读取第一页，多页文件按第一页信息命名；合并则保留每个可读取页面
- 加密 PDF 需要先解密，损坏文件会记录为失败

## License

MIT License
