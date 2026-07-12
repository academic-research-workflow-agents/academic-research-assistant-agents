# Reading Subagent Guide

## Role
Build a reusable evidence base from academic sources: paper cards, evidence ledgers, citation metadata, and query summaries.

## Case Layout

```text
examples/<thesis_case>/<child_case>/
  AGENTS.md
  README.md
  inputs/
  manifests/
  outputs/
```

The shared copy includes only `examples/example_thesis/example_case/`.

## Source Rules
Shared manifests may contain citation keys, titles, status fields, and case-local relative paths. Machine-local paths and private source files must stay outside shared packages.

## Outputs
Evidence ledgers should be concise and claim-focused. Do not include full paper text, private annotations, or external absolute paths.