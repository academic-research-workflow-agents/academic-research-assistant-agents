# Codex-data_panel

这是一个通用能力目录，用来把上游原始表整理成可人工核查的基础面板。

它不是大多数真实课题的直接入口。你如果在处理具体课题，应优先去对应的 `../../examples/<thesis_case>/<child_case>/`。

## 这里提供什么
- 基础 panel 的通用处理能力
- 对应阶段的本地脚本入口

## 本地入口

```powershell
python scripts/merge_lp_sheets.py --input-path <raw_workbook.xlsx> --output-dir <merge_dir>
python scripts/reshape_lp_to_panel.py --merged-path <merged.xlsx> --panel-dir <panel_dir> --exceptions-dir <exceptions_dir>
```

## 输出位置
结果通常写到 `outputs/panel/`
