---
name: beamer-template-adaptation
description: Adapt, preserve, and smoke-test reusable Beamer template source cases. Use when Codex needs to import an external Beamer template, preserve provenance, create a school or brand-specific template source case, update .sty files, or keep a template source case separate from concrete deck content.
---

# Beamer Template Adaptation

## Workflow
1. Locate the active template source case under `Subagent_template/examples/<template_case>/<child_case>/`.
2. Preserve upstream files in `source/` and record provenance in `manifests/`.
3. Keep a smoke `source/main.tex` that compiles without private deck content.
4. Put institution or brand defaults only in the template source case, never in root files.
5. Do not modify a template source case as part of normal deck compilation. Copy it into a deck-local worktree first.

## Editing Rules
- Prefer small `.sty` adaptations over one-off geometry inside slides.
- Keep logo paths local to the template source case.
- Use placeholder author/title metadata for smoke decks.
- Keep license and attribution notes close to the imported template.

## Validation
Run:

```powershell
npm run check-source -- --case <template-child-case>
npm run render -- --case <template-child-case>
```
