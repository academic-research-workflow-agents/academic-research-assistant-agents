# LaTeX Formatting Subagent Guide

## Role
`Subagent_format_latex` performs deterministic layout work on user-provided source files.

Allowed work:
- copy explicit LaTeX sources without changing text
- convert explicit Markdown sources to LaTeX with Pandoc
- materialize declared CSV tables, figures, bibliography files, and TeX fragments
- compile case-local previews and report technical diagnostics

Disallowed work:
- create or complete academic正文
- add claims, explanations, findings, transitions, abstracts, or conclusions
- process a source file that is not declared in the active manifest

## Case Layout

```text
examples/<research_case>/<child_case>/
  inputs/
  assets/
  manifests/source_manifest.json
  outputs/
```

`inputs/` and the manifest are the source of truth. Everything under `outputs/` is reproducible and disposable.

## Integrity Contract
Every processed source must record its SHA256, converter, input path, and output path. Do not add placeholder正文 when an input is empty or missing; fail with a clear error instead.
