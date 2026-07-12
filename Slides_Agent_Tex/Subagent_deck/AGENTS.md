# Subagent_deck Contract

## Role
`Subagent_deck` owns concrete Beamer deck cases.

It is responsible for:

- slide narrative and section structure
- `source/main.tex`
- `source/sections/*.tex`
- `source/*.bib`
- deck-specific figures and assets
- case-local deck instructions

It is not responsible for:

- editing authoritative template source cases
- replacing integration mapping
- owning compile and render diagnostics

## Case Architecture
Deck work lives under:

```text
examples/<slide_case>/<child_case>/
```

The `slide_case` namespace can identify a project. The `child_case` is the runnable deck case.

## Source Contract
The deck source should stay independent from the copied template worktree. Build outputs and copied templates belong under `outputs/`.
