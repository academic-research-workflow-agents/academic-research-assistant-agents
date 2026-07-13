# Subagent_evidence

这一层把学术来源整理成可核验的证据卡和 evidence ledger。

## 输入

- `ref.bib`，或放在 `inputs/sources/` 的 case-local PDF
- 当前 query 需要关注的信息条目

## 常用入口

```powershell
python scripts/bootstrap_evidence_case.py --case-root examples/<research_case>/<child_case>
python scripts/build_source_manifest.py --case-root examples/<research_case>/<child_case>
python scripts/ensure_source_corpus.py --case-root examples/<research_case>/<child_case>
python scripts/run_evidence_query.py --case-root examples/<research_case>/<child_case> --info-item <item>
```

Query 输出只能组合 evidence ledger 中已有的短摘要，并保留引用键与页码。缺少证据时应报告缺口，不能自行补充主张。
