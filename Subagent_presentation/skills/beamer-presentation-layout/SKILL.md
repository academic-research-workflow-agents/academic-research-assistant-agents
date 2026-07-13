---
name: beamer-presentation-layout
description: Assemble evidence-bound Beamer presentation cases from registered user materials. Use when Codex must arrange supplied text, citations, equations, tables, figures, or visual structure into TeX frames without adding research claims or conclusions.
---

# Beamer Presentation Layout

1. Work inside `Subagent_presentation/examples/<research_case>/<child_case>/`.
2. Read `manifests/presentation_manifest.json` before editing source files.
3. Use only registered sources and one of `verbatim`, `extract`, `compress`, or `layout` for each slide.
4. Add exactly one `\label{slide:<id>}` to every frame and keep it synchronized with `slides[]`.
5. Preserve citations, numerical values, equations, and causal boundaries from the source material.
6. Stop and request materials when no source supports the requested visible information.
7. Run source checks before rendering.
