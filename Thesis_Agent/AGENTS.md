# Thesis Agent Root Guide

## Role
`Thesis_Agent` is a shareable thesis-workflow framework. It coordinates subagents for reading, empirical asset preparation, regression work, writing, integration, and checks.

Default user-facing language: Chinese.

## Routing
Classify the request before doing substantial work:

1. `query_or_check` -> `Subagent_check`
2. `reading` -> `Subagent_read_paper`
3. `empirical_asset_building` -> `Subagent_process_data` or `Subagent_regress_stata`
4. `thesis_writing` -> `Subagent_write_latex`
5. `integration` -> `Subagent_integrate`

## Case Contract
Real work belongs under:

```text
Subagent_<name>/examples/<thesis_case>/<child_case>/
```

The outer case is a namespace. The child case is the working unit.

This shared copy contains only synthetic examples under `example_thesis/example_case`.

## Privacy Contract
Do not store personal data, private project names, institution-specific templates, generated outputs, local absolute paths, logs, backups, or archived runs in the framework layer. Case-local private material must stay outside this shared package.

## Framework Top Level
The root level should contain only framework files, subagents, common contracts, generic scripts, and example cases.
