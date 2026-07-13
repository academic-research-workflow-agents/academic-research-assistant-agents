# Check Subagent Guide

## Role
`Subagent_check` is the read-only validation layer for one `research_case`.

It validates coordination references, linked case paths, manifest structure, provenance status, and technical reports. It writes reports only inside its own child case and never edits a checked business case.

The checker must not create replacement正文 or instructions that add claims, explanations, findings, or conclusions.

## Case Layout

```text
examples/<research_case>/<child_case>/
  manifests/research_check_manifest.json
  outputs/research_check_report.json
  outputs/research_check_report.md
```
