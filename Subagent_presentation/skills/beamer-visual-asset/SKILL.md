---
name: beamer-visual-asset
description: Organize and validate source-bound visual assets for Beamer presentations and templates. Use when Codex must add, reference, or check figures, diagrams, screenshots, logos, or text-free generated images.
---

# Beamer Visual Asset

- Keep visible slide text in TeX, not inside generated images.
- Register the material that supports each visual in the presentation manifest.
- Store case figures under `assets/figures/` and reusable generic template assets under `templates/`.
- Use trusted local or official assets for logos and preserve provenance.
- Prefer vector or high-resolution images for PDF output.
- Confirm every `\includegraphics{...}` path resolves after template overlay.
