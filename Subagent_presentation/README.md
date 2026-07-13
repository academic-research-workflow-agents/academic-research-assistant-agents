# Subagent_presentation

单一的 TeX/Beamer 演示文稿 subagent，输出可编辑 TeX、PDF 和 PNG 预览。

## Case

```text
examples/<research_case>/<child_case>/
```

每个 frame 都要在 `presentation_manifest.json` 中登记来源和变换类型。只有主题、没有材料时不会继续组装可见信息。

## 命令

从仓库根运行：

```powershell
npm run presentation:inspect -- --case examples/example_research/example_presentation
npm run presentation:check-source -- --case examples/example_research/example_presentation
npm run presentation:render -- --case examples/example_research/example_presentation
npm run presentation:render:png -- --case examples/example_research/example_presentation
```
