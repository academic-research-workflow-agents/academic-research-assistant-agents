# Subagent_template Contract

## Role
`Subagent_template` owns reusable Beamer template source cases.

It is responsible for:

- importing external Beamer templates
- preserving template provenance and license notes
- adapting templates into institution or brand source cases
- keeping template smoke decks compilable

It is not responsible for:

- writing concrete deck content
- storing private project material
- managing deck-to-template coordination beyond template metadata

## Case Architecture
Template work lives under:

```text
examples/<template_case>/<child_case>/
```

The `child_case` is the actual template source case.

## Template Source Contract
A template source case should keep:

- `source/main.tex`
- `source/theme/*.sty` or template-level `.sty` files
- `source/*.bib` when the smoke deck cites references
- local figures or logos required for smoke compilation
- `manifests/`
- `outputs/`

Template source cases are authoritative and should not be modified by deck compilation. Deck builds must use a copied worktree.
