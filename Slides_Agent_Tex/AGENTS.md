# Slides_Agent_Tex Root Agent Guide

## Role
`Slides_Agent_Tex` is a TeX/Beamer-first slide authoring system.

The root layer is framework-only. It routes work to subagents, maintains source-of-truth rules, and prevents institution-specific or project-specific state from leaking into the generic framework.

Default user-facing communication language: Chinese.

Internal contracts, scripts, and skills may use English or bilingual wording when that improves precision.

## First Routing Rule
Root must classify the request before doing substantial work:

1. `template`
2. `deck`
3. `integration`
4. `check`
5. `query_or_check`

Routes:

- `template` -> `Subagent_template`
- `deck` -> `Subagent_deck`
- `integration` -> `Subagent_integrate`
- `check` or `query_or_check` -> `Subagent_check`

## Source Of Truth Contract
The durable editable source is:

- `source/main.tex`
- `source/sections/*.tex`
- `source/theme/*.sty`
- `source/*.bib`
- `assets/`
- `manifests/`

Generated PDFs, logs, PNG previews, and template worktrees under `outputs/` are artifacts only.

Do not edit generated PDFs or converted presentation files as the primary workflow. If the user asks for a change after rendering, return to source files.

## Three-Layer Architecture
Layer 1 is this generic framework.

Layer 2 stores institution or brand template source cases under `Subagent_template/examples/<template_case>/<child_case>/`.

Layer 3 stores concrete deck cases under `Subagent_deck/examples/<slide_case>/<child_case>/`.

Root files must use neutral placeholders such as:

```text
examples/<slide_case>/<child_case>/
```

Do not put concrete school, brand, or private project defaults in root contracts.

## Template Copy Rule
Template source cases are authoritative sources. A concrete deck must not directly edit them during normal build work.

Before compiling a deck, copy the selected template source into the deck-local worktree:

```text
outputs/build/template-worktree/
```

Then overlay the deck source and assets into that worktree and compile there.

## Case Architecture
All real work lives under a subagent `examples/` tree:

```text
Subagent_<name>/examples/<slide_case>/<child_case>/
```

The outer `slide_case` is a namespace. The inner `child_case` is the actual working unit.

Do not treat `examples/<slide_case>/` as a runnable case.

## Public Visibility Rule
Upper-layer documents should not expose private case names or institution-specific defaults.

Specific school, brand, or project details belong in their own child cases.

## Root Minimal Structure
The root level is limited to:

- `AGENTS.md`
- `README.md`
- `package.json`
- `scripts/`
- `skills/`
- `Subagent_template/`
- `Subagent_deck/`
- `Subagent_integrate/`
- `Subagent_check/`

Root must not store run outputs, case-specific defaults, or temporary debug artifacts.
