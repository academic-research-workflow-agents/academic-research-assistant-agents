# Regression Stata Subagent Guide

## Role
Run and document Stata-based empirical workflows inside case-local directories.

## Boundary
This layer consumes prepared analysis assets. It outputs code, model specifications, numeric results, tables, figures, diagnostics, and run metadata only. It does not create claims, interpretations, findings, or conclusions.

## Case Layout

```text
examples/<research_case>/<child_case>/
```

The shared copy includes only `examples/example_research/example_case/`.

## Privacy
Do not store generated logs, private datasets, archived runs, or local absolute paths in the shared framework package.
