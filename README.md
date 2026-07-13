# 学术研究辅助 AI Agents

English name: **Academic Research Assistant AI Agents**

这是一个单一的学术研究辅助框架，把可审计的研究流程拆成七个协作 subagent：

- `Subagent_evidence`：学术来源、证据卡、引用和页码记录
- `Subagent_process_data`：数据清理、拼接和分析资产
- `Subagent_regress_stata`：Stata 执行、表图、诊断和结构化结果
- `Subagent_format_latex`：用户原文的 LaTeX 排版、表图和参考文献处理
- `Subagent_presentation`：有来源约束的 TeX/Beamer 演示文稿
- `Subagent_integrate`：按请求组合所需能力
- `Subagent_check`：路径、契约、来源追踪、编译和边界检查

## 内容边界

框架可以从用户提供的学术来源中提取和归类证据，可以执行数据与实证计算，也可以把用户原文排成 LaTeX 文档。

它不会创建可直接提交的学术正文，也不会新增研究主张、发现、解释或结论。演示文稿中的可见信息必须来自已登记的用户材料或证据资产。

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

## 检查与发布

```powershell
npm run check:terminology
python -m pytest
npm run preview:check
npm run release:private -- -Version 0.2.0
```

发布脚本只生成一个 `Academic_Research_Assistant_AI_Agents_v<version>.zip`。

## Private 与 Public Preview

本 private 仓库是完整产品和 public preview 的唯一内容源。公开内容维护在
`distribution/public-preview/`，通过以下命令单向同步到 sibling preview 仓库：

```powershell
npm run preview:sync -- --dry-run
npm run preview:sync
# 在 preview 仓库审阅并提交受控改动后：
npm run preview:check
```

同步器只覆盖 allowlist 中的公开文件并清理不再公开的 tracked 文件；目标仓库中不属于
上一份同步 manifest 的未跟踪文件不会被覆盖或删除。public preview 只包含说明、静态契约记录和一个极小的
证据约束型 Beamer 演示，不包含完整 subagent、skills 或 private 工作流脚本。

## 隐私

仓库只保存通用框架、脚本、契约、skills 和 synthetic examples。不要提交真实研究材料、真实数据、机构专属模板、运行输出、日志、归档、API keys 或本地私人信息。
