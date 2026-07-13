---
name: beamer-template-adaptation
description: Adapt, preserve, and smoke-test reusable Beamer templates. Use when Codex must import a template, preserve provenance and licensing, update .sty files, or maintain a generic template separately from presentation cases.
---

# Beamer Template Adaptation

1. Store reusable framework templates under `Subagent_presentation/templates/<template_id>/`.
2. Preserve upstream source, provenance, and license notes.
3. Keep a neutral smoke `source/main.tex` with placeholder metadata.
4. Keep institution or brand material in private storage, not in the shared framework.
5. Never modify the authoritative template during a normal case render; the renderer copies it into a case-local worktree.
