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

## 检查

```powershell
npm run check:terminology
npm run test:presentation
python -m pytest
```

## 隐私

本仓库作为内部研究辅助框架，只保存通用脚本、契约、skills 和 synthetic examples。真实研究材料应留在受控的私有工作目录中；不要提交真实数据、机构专属模板、运行输出、日志、归档、API keys 或本地私人信息。
