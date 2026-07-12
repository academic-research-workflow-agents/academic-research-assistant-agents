# Regression Stata Subagent Guide

## Role
Run and document Stata-based empirical workflows inside case-local directories.

## Boundary
This layer consumes prepared analysis assets. It does not perform upstream input preparation, reading-card production, or manuscript writing.

## Case Layout

```text
examples/<thesis_case>/<child_case>/
```

The shared copy includes only `examples/example_thesis/example_case/`.

## Privacy
Do not store generated logs, private datasets, archived runs, or local absolute paths in the shared framework package.