---
name: paper-read
description: Read academic papers into structured, share-safe cards and evidence ledgers.
---

# Paper Read Skill

Use this skill when a reading case needs paper cards, evidence ledgers, citation keys, and query-ready summaries.

## Workflow

1. Read `manifests/paper_manifest.json` for shared-safe paper metadata.
2. Create one card per selected source in the case-local card directory.
3. Record claims in an evidence ledger with citation keys, page spans, confidence, and short summaries.
4. Keep machine-local paths and private source files outside shared manifests.

## Privacy

Do not write local absolute paths, private filenames, personal notes, or full copyrighted paper text into shared outputs.