# Evidence Manifest Contract

## `manifests/case_manifest.json`

- `case_id`: clean case identifier
- `ingest_mode`: `manual_entry | linked_bib | mixed`
- `default_language`: default output language
- `content_mode`: fixed to `evidence_bound`
- `source_input_root`: case-local source input directory, if used
- `output_policy`: case-local evidence and query locations

## `manifests/source_manifest.json`

Shared-safe manifest fields:

- `citation_key`
- `title`
- `ingest_source`
- `attachment_status`
- `selected_attachment_kind`
- `card_status`
- `selection_stage`

Query summaries may only reuse evidence-ledger rows with citation keys and page spans. They are research notes, not submit-ready academic正文.

## Privacy Rule

Shared manifests must not contain local absolute paths, private filenames, or private source locations. Keep machine-local indexes outside shared packages.
