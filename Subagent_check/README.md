# Subagent_check

这一层只读检查 coordination manifest 及其已链接 child cases。

```powershell
python scripts/bootstrap_check_case.py --case-root examples/<research_case>/<child_case>
python scripts/run_research_check.py --case-root examples/<research_case>/<child_case>
```

报告只写入当前 check case 的 `outputs/`。
