# Subagent_integrate

这一层用于查看同一 `research_case` 在各业务 subagent 下已有的 child case，并按本次请求给出下一步。

```powershell
python scripts/bootstrap_integration_case.py --case-root examples/<research_case>/<child_case>
python scripts/refresh_coordination_manifest.py --case-root examples/<research_case>/<child_case>
python scripts/scan_research_cases.py --case-root examples/<research_case>/<child_case>
```

先在 coordination manifest 的 `requested_capabilities` 中列出本次真正需要的能力；未列出的能力不会阻塞流程。
