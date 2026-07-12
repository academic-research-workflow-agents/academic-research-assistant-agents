# Reading Manifest Contract

## `manifests/case_manifest.json`

- `case_id`: clean case identifier
- `ingest_mode`: `manual_entry | linked_bib | mixed`
- `default_language`: default output language
- `paper_input_root`: case-local paper input directory, if used
- `output_policy`: case-local evidence and query locations

## `manifests/paper_manifest.json`

Shared-safe manifest fields:

- `citation_key`
- `title`
- `ingest_source`
- `attachment_status`
- `selected_attachment_kind`
- `card_status`
- `selection_stage`

## Privacy Rule

Shared manifests must not contain local absolute paths, private filenames, or private source locations. Keep machine-local indexes outside shared packages.