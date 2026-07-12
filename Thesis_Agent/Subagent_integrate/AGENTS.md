# Integration Subagent Guide

## Role
Coordinate a thesis case across reading, data preparation, regression, writing, and checks.

## Scope
This subagent owns only its own case directory:

```text
examples/<thesis_case>/<child_case>/
```

It records mappings, readiness gates, and next actions. It does not edit other subagents' private work directly.

## Example
Use `examples/example_thesis/example_case/` as the shared skeleton.

## Privacy
Do not record local absolute paths, private project names, generated outputs, archived runs, or external workspace references in shared manifests.