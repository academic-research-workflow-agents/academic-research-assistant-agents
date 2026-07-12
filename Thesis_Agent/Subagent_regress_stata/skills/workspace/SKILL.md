---
name: regression-subagent-workspace
description: >
  Use when working inside Subagent_regress_stata. This is the
  only user-facing regression subagent. Prefer workspace-local skills for asset
  scan, model registry, Stata execution, result assembly, follow-up screening,
  and graph export.
---

# Regression Subagent Workspace

This workspace is Stata-first and skill-oriented.

## Core rule

The complete regression workflow belongs to this subagent.

Skills are reusable components only. Do not let a skill replace the full regression flow.

## Preferred internal skills

- `skills/skill_asset_scan/`
- `skills/skill_model_registry/`
- `skills/skill_stata_executor/`
- `skills/skill_result_assembly/`
- `skills/skill_did_advanced/`
- `skills/skill_followup_screen/`
- `skills/skill_graph_export/`
- `skills/stata/`

## Execution order

1. Read `AGENTS.md`
2. Inspect `data/`
3. Scan and summarize candidate assets
4. Confirm shared model design
5. Generate a baseline manifest and baseline master do-file
6. Run baseline batch and build lightweight summary
7. If the user selects a follow-up set, generate a follow-up manifest and follow-up master do-file
8. Only when the workflow converges to a final design, export a single-design do-file
9. Write outputs under `output/results/` and logs under `output/runtime/`

