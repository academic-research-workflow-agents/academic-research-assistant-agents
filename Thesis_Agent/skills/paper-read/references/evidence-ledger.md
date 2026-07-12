# Evidence Ledger Contract

Canonical file:
- `outputs/evidence/evidence_ledger.jsonl`

Each row should contain:

```json
{
  "citation_key": "example2024paper",
  "paper_title": "Example Paper",
  "source_type": "paper_card",
  "source_pdf": "linked_bib",
  "source_card_md": "cards/example2024paper.md",
  "info_item": "controls",
  "claim_summary": "Controls include firm size, leverage, and age.",
  "verbatim_excerpt": "We control for firm size, leverage, and age in all specifications.",
  "page_span": "12",
  "confidence": 0.92
}
```

Guidelines:
- Use one row per audit-ready claim.
- Prefer multiple narrow rows over one overloaded row.
- Keep `confidence` conservative when the paper is indirect or ambiguous.
- Reuse canonical `info_item` labels whenever possible.
