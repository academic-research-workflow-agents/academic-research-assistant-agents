# Subagent_format_latex

这一层只处理用户提供文本的机械排版。

## 开始方式

1. 把用户文件放入 `examples/<research_case>/<child_case>/inputs/`。
2. 在 `manifests/source_manifest.json` 中逐项登记来源、格式和目标路径。
3. 运行转换、资产物化和预览编译脚本。

```powershell
python scripts/convert_sources_to_latex.py --case-root examples/<research_case>/<child_case>
python scripts/materialize_assets.py --case-root examples/<research_case>/<child_case>
python scripts/compile_preview.py --case-root examples/<research_case>/<child_case>
```

缺少原文时，这一层不会补充正文，只会报告缺失项。
