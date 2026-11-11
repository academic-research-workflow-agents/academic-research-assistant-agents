# 学术研究辅助 AI Agents

English name: **Academic Research Assistant AI Agents**

这是一个学术研究辅助框架，把研究流程拆成七个协作 subagent：

- `Subagent_evidence`：学术文献、证据卡、引用和页码记录
- `Subagent_process_data`：数据清理、拼接和分析资产
- `Subagent_regress_stata`：Stata 执行、表图、诊断和结构化结果
- `Subagent_format_latex`： LaTeX 排版、表图和参考文献处理
- `Subagent_presentation`： TeX/Beamer 演示文稿
- `Subagent_integrate`：按请求组合所需能力
- `Subagent_check`：路径、契约、来源追踪、编译和边界检查

## 内容边界

从用户提供的学术文献中提取和归类信息
对用户提供的原始数据进行清洗处理和实证分析
将用户提供的原始文稿排成 LaTeX 文档或TeX/Beamer演示文稿

## Case 结构

```text
Subagent_<name>/examples/<research_case>/<child_case>/
```

共享仓库中的 `example_research/example_case` 只用于验证结构。真实材料应放在私有工作目录。

## Beamer 命令

```powershell
npm run presentation:inspect -- --case examples/example_research/example_presentation
npm run presentation:check-source -- --case examples/example_research/example_presentation
npm run presentation:render -- --case examples/example_research/example_presentation
npm run presentation:render:png -- --case examples/example_research/example_presentation
```

## 检查

```powershell
npm run check:terminology
npm run test:presentation
python -m pytest
```

## 隐私

本仓库作为内部研究辅助框架，只保存通用脚本、契约、skills 和 synthetic examples。真实研究材料应留在受控的私有工作目录中；不要提交真实数据、机构专属模板、运行输出、日志、归档、API keys 或本地私人信息。

## 安装与环境配置（Windows PowerShell）

两个仓库使用相近的核心运行环境。建议 Python 3.12 64 位，Node.js 20 或以上。Python 3.8 32 位不适合作为本项目的数据分析和 OCR 环境。

| 用途 | 必需环境 |
| --- | --- |
| 数据、PDF 文本、校验 | Python 3.12 x64，`requirements.txt` 中的 NumPy、pandas、openpyxl、xlrd、pypdf、PyYAML、pytest |
| 扫描 PDF OCR | 另装 `requirements-ocr.txt`，含 PyMuPDF、RapidOCR 与 ONNX Runtime 依赖 |
| 演示脚本 | Node.js >=20，npm 随官方 Node.js 安装器提供；当前 package.json 无第三方 npm 依赖 |
| Stata 实证 | 已授权的 Stata 17+，配置 `REGRESSION_STATA_PATH`；按模型安装 ado 包 |
| LaTeX / Beamer | TeX Live 或 MiKTeX，确保 `xelatex`、`latexmk`、`bibtex`、`biber` 可运行；latexmk 需要 Perl |
| PDF 转 PNG | Poppler 的 `pdftoppm` |
| 公共仓库的 Markdown 转换 | Pandoc，处理 Markdown 转 LaTeX 时需要 |

在各仓库根目录执行（先安装 Python，再打开新终端）。

```powershell
winget install --id Python.Python.3.12 -e --source winget --scope user
winget install --id OpenJS.NodeJS.LTS -e --source winget
py -3.12 -m pip install -r requirements.txt
# 需要扫描件 OCR 时执行
py -3.12 -m pip install -r requirements-ocr.txt
py -3.12 --version
```

Stata 使用官方安装介质和有效许可证。把以下占位路径替换为实际可执行文件路径，再在同一终端启动 Agent。

```powershell
$env:REGRESSION_STATA_PATH = 'C:\path\to\StataMP-64.exe'
```

在 Stata 中安装核心外部包，已有包可用 `which reghdfe` 等命令检查。

```stata
ssc install ftools
ssc install reghdfe
ssc install psmatch2
ssc install estout
```

其他估计方法所需的 ado 包按任务补装。依赖清单给出兼容版本范围，精确复现时请在受控工作目录保存 `py -3.12 -m pip freeze` 的结果。真实材料、许可证、机器路径和运行日志保留在本地。

公共仓库在根目录执行 `py -3.12 -m pytest`、`node scripts/check-terminology.mjs` 和 `node --test Subagent_presentation/tests/*.test.mjs`。上述现有 npm 命令也可继续使用。

Stata 版本说明。当前生成器与安装检查脚本声明 `version 17.0`。Stata 16 是否兼容仍需在有效许可证下用合成案例验证；仅修改版本声明不足以证明模型流程兼容。Python、文献、数据和排版功能可分别使用。
