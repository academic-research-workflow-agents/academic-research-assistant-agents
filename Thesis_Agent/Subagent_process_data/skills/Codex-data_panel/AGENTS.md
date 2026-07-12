# Data Panel Workflow Guide For Agents

## Role
This skill provides the generic base-panel stage inside `Subagent_process_data`.

- build a review-ready base panel from upstream raw tables
- expose the minimal capability contract, neutral demo, and scripts for that stage

It is a capability-layer skill, not a user-case landing zone.

## Routing Rule
Do not tell the user to remain in this skill directory for a real case.

If the request is case-specific, route to the matching directory under `../../examples/<thesis_case>/<child_case>/`.

## Generic Entrypoints
Use local stage entrypoints from this skill directory:

```powershell
python scripts/merge_lp_sheets.py --input-path <raw_workbook.xlsx> --output-dir <merge_dir>
python scripts/reshape_lp_to_panel.py --merged-path <merged.xlsx> --panel-dir <panel_dir> --exceptions-dir <exceptions_dir>
```

Domain-specific branch-generation stage entrypoints live under `../../examples/<thesis_case>/<child_case>/`.

## Cases / Example Entrances
- real thesis work -> `../../examples/<thesis_case>/<child_case>/`
- empty scaffold example -> `../../examples/_empty_thesis_case/_empty_child_case/`

## Input Contract
For the base-panel stage, confirm:
- the upstream raw workbook or table set to transform
- the assets directory and outputs directory if the defaults are not intended

Do not assume thesis-specific file names as the default generic input contract.

## Output Contract
Base-panel stage writes review-ready outputs under `outputs/panel/`, including:
- merged intermediate files
- panel files
- exception files
- human-review hints

## Boundary Rules
This skill must not:
- replace the parent `Subagent_process_data` routing contract
- assume a government-guided-fund or thesis-specific branch definition by default
- present itself as the correct stopping point for a concrete user scenario

If the user clearly needs a domain-specific branch workflow, route them to a domain example under `../../examples/<thesis_case>/<child_case>/`.

## Examples
Domain-specific branch examples belong under `../../examples/<thesis_case>/<child_case>/`.

Do not ask users to stay in this skill once the task is clearly tied to a real thesis case.

