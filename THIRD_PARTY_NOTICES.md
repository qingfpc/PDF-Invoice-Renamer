# Third-party notices / 第三方许可说明

The MIT [LICENSE](LICENSE) applies to the source code in this repository. Dependencies keep their own licenses. It does not replace the licenses of components bundled in Windows EXEs.

本仓库源码使用 MIT [许可证](LICENSE)。依赖库保留各自的许可；MIT 许可不替代 Windows EXE 中打包组件的许可。

The merger EXEs include PyMuPDF 1.26.4 and MuPDF 1.26.7. Their open-source distributions use GNU AGPLv3; PyMuPDF also offers commercial licensing. See the [upstream licensing statement](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) and the original `COPYING` included in the release's `THIRD_PARTY_LICENSES.zip`. Preserve applicable notices when redistributing the EXEs.

合并程序包含 PyMuPDF 1.26.4 和 MuPDF 1.26.7，其开源发行版使用 GNU AGPLv3；PyMuPDF 也提供商业许可。详见[上游许可说明](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)和 Release 的 `THIRD_PARTY_LICENSES.zip` 中的原始 `COPYING`。再次分发 EXE 时须保留适用的许可说明。

## Source and build references / 源码与构建资料

The release tag provides this project's source, pinned dependencies, and `build.ps1`. The following references identify the components used by the v3.0.0 Windows build. Original license texts are copied from the installed distributions into `THIRD_PARTY_LICENSES.zip`, including PDFium's bundled dependency notices, Python's license, and PyInstaller's exception.

Release 标签提供本项目源码、固定依赖版本及 `build.ps1`。以下是 v3.0.0 Windows 构建使用的组件；`THIRD_PARTY_LICENSES.zip` 收录安装发行包中的原始许可文本，包括 PDFium 的依赖说明、Python 许可和 PyInstaller 的例外条款。

| Component / 组件 | Version / 版本 | Source / 源码 |
| --- | --- | --- |
| Python | 3.12.13 | [CPython](https://github.com/python/cpython/tree/v3.12.13) |
| pdfplumber | 0.11.9 | [Distribution and source](https://pypi.org/project/pdfplumber/0.11.9/#files) |
| pdfminer.six | 20251230 | [Distribution and source](https://pypi.org/project/pdfminer.six/20251230/#files) |
| PyMuPDF | 1.26.4 | [PyMuPDF](https://github.com/pymupdf/PyMuPDF/tree/1.26.4) |
| MuPDF | 1.26.7 | [MuPDF](https://github.com/ArtifexSoftware/mupdf/tree/1.26.7) |
| pypdfium2 | 5.13.0 | [Source and PDFium build information](https://github.com/pypdfium2-team/pypdfium2/tree/5.13.0) |
| Pillow | 12.3.0 | [Distribution and source](https://pypi.org/project/pillow/12.3.0/#files) |
| cryptography | 50.0.2 | [Distribution and source](https://pypi.org/project/cryptography/50.0.2/#files) |
| cffi | 2.1.1 | [Distribution and source](https://pypi.org/project/cffi/2.1.1/#files) |
| pycparser | 3.0 | [Distribution and source](https://pypi.org/project/pycparser/3.0/#files) |
| charset-normalizer | 3.5.2 | [Distribution and source](https://pypi.org/project/charset-normalizer/3.5.2/#files) |
| PyInstaller | 6.16.0 | [PyInstaller](https://github.com/pyinstaller/pyinstaller/tree/v6.16.0) |

Build and test tools are pinned in `requirements-dev.txt` and `constraints.txt`. Their inclusion in the development environment does not mean every tool is bundled in each EXE.

构建和测试工具版本见 `requirements-dev.txt` 与 `constraints.txt`；安装到开发环境不表示每个工具都被打包进每个 EXE。
