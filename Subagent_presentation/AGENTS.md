# Presentation Subagent Guide

## Role
`Subagent_presentation` assembles TeX/Beamer presentations from registered user materials and evidence assets.

It is one subagent with internal templates, skills, scripts, and case examples. It does not contain nested agents.

## Evidence-Bound Contract
- Require `manifests/presentation_manifest.json` with `content_mode: evidence_bound`.
- Require every visible frame to contain exactly one `\label{slide:<id>}`.
- Require every slide entry to reference at least one registered source.
- Allow only `verbatim`, `extract`, `compress`, and `layout` transforms.
- Stop and request source materials when a topic is provided without registered inputs.
- Do not add research claims, findings, explanations, or conclusions.

## Source Of Truth

```text
source/main.tex
source/sections/*.tex
source/theme/*.sty
source/*.bib
assets/
inputs/
manifests/presentation_manifest.json
```

PDFs, PNG previews, logs, and build worktrees under `outputs/` are artifacts only.

## Internal Templates
Reusable generic templates live under `templates/<template_id>/`. Institution-specific material belongs in private case-local storage and must not enter the framework.
