# Panel Builder Internal Guide

## Role
This skill is the internal provider-driven panel-builder shell used by `Subagent_process_data`.

It is a capability-layer shell with provider-neutral contract, neutral demo, scripts, and tests.

It is not a standalone top-level workflow or a user-case landing directory.

## When To Use
Use this skill when an agent needs:
- a local script entrypoint around the parent panel-builder flow
- generic request examples for panel-build specs
- local tests for the panel-builder shell

Do not route ordinary users here first if the request is already tied to a concrete case.

## Preferred Entrypoints
Preferred parent entrypoint:

```powershell
python ../../../scripts/build_regression_panels.py --spec-file <spec.json>
```

Local script entrypoint:

```powershell
python scripts/run_panel_builder_batch.py
```

Treat the local script as a debugging-only entrypoint. It is not the primary explanation path.

## Cases / Example Entrances
- real thesis work -> `../../examples/<thesis_case>/<child_case>/`
- empty scaffold example -> `../../examples/_empty_thesis_case/_empty_child_case/`

## Generic Contract
This skill assumes a provider-driven build flow based on:
- variable assets
- build spec inputs
- key-template compatible grouping

Generic examples should stay provider-neutral where possible.

Prioritize these local references:
- `examples/requests/`
- `tests/test_panel_builder.py`
- `../../contracts/`
- `../../examples/_demo_thesis_case/_demo_provider_case/requests/demo_build_spec.json`

## Boundary Rules
This skill must not:
- present thesis-specific providers as the default example
- describe old-case fixtures as the current primary contract
- describe local scripts as the current primary entrypoint
- describe itself as the correct place for a concrete user scenario

`assets/` may still contain generic fixtures. The stable contract lives in the parent subagent contracts and case-local provider catalogs.

## Examples
Domain-specific examples belong under `../../examples/<thesis_case>/<child_case>/`.

Use those example directories when the request is clearly tied to a specialized provider or specialized panel family.

Do not expose local debugging emphasis, local test fixtures, or provider-neutral shell details unless that information is necessary to complete the agent task.

