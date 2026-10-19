# 学术研究辅助 AI Agents

English name: **Academic Research Assistant AI Agents**

这是一个单一的学术研究辅助框架，把可审计的研究流程拆成七个协作 subagent：

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
