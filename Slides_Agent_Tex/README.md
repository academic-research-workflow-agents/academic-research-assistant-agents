# Slides_Agent_Tex

This is a shareable TeX/Beamer-first slide authoring agent framework.

The durable source of truth is:

- `source/main.tex`
- `source/sections/*.tex`
- `source/*.bib`
- `assets/`
- `manifests/`

Generated PDFs, logs, PNG previews, build worktrees, archived runs, and brand templates are not included in this shared copy.

## Example

```text
Subagent_deck/examples/example_slide/example_beamer_deck/
```

Common commands:

```powershell
npm run inspect -- --case Subagent_deck/examples/example_slide/example_beamer_deck
npm run check-source -- --case Subagent_deck/examples/example_slide/example_beamer_deck
npm run render -- --case Subagent_deck/examples/example_slide/example_beamer_deck
```