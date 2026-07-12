# Writing Subagent Guide

## Role
Maintain manuscript source, chapter manifests, bibliography handoffs, and local build instructions for a thesis-writing case.

## Case Layout

```text
examples/<thesis_case>/<child_case>/
  AGENTS.md
  README.md
  manuscript/
  assets/
  manifests/
```

The shared copy includes only `examples/example_thesis/example_case/`.

## Source Of Truth
Editable manuscript files and manifests are source. Generated PDFs, rendered assets, logs, archives, and build worktrees are artifacts and should not be shared as framework content.

## Privacy
Do not include institution-specific templates, signatures, personal metadata, private data, generated outputs, or local absolute paths in the shared framework layer.