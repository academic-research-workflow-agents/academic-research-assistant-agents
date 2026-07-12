---
name: beamer-deck-authoring
description: Author concrete Beamer deck cases. Use when Codex needs to write or revise a specific slide deck, including source/main.tex, source/sections/*.tex, citations, bibliography, figures, equations, tables, speaker structure, or academic presentation narrative.
---

# Beamer Deck Authoring

## Workflow
1. Work inside `Subagent_deck/examples/<slide_case>/<child_case>/`.
2. Keep durable content in `source/main.tex`, `source/sections/*.tex`, `source/*.bib`, and `assets/`.
3. Use the template selected by the case manifest. Do not copy template styling manually into deck source unless the case explicitly owns a local override.
4. Keep visible slide text concise; move long explanation into notes or backup slides.
5. Prefer Beamer-native tables, equations, blocks, and figures over screenshots of text.

## Source Guidelines
- Keep section files small and ordered.
- Keep bibliography local to the deck case unless an integration manifest explicitly provides another source.
- Use relative asset paths that work after the deck is overlaid into `outputs/build/template-worktree/`.

## Validation
Run:

```powershell
npm run check-source -- --case <deck-child-case>
npm run render -- --case <deck-child-case>
```
