# Evidence Subagent Guide

## Role
Build a reusable, citation-bound evidence base from academic sources.

Allowed outputs:
- source inventory and citation metadata
- one evidence card per selected source
- evidence ledger rows with citation key, page span, confidence, and concise summary
- focused query summaries assembled only from ledger rows

This layer must not turn evidence records into submit-ready academic正文 or add claims not supported by the cited source.

## Case Layout

```text
examples/<research_case>/<child_case>/
  inputs/sources/
  evidence_cards/
  manifests/
  outputs/evidence/
  outputs/queries/
```

Private PDFs and machine-local paths stay outside shared manifests. Shared outputs must not contain full copyrighted source text.
