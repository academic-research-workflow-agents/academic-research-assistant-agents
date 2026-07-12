---
name: beamer-visual-asset
description: Manage visual assets for Beamer decks and templates. Use when Codex needs to add, organize, reference, or check logos, figures, diagrams, screenshots, or generated text-free images for a TeX/Beamer slide system.
---

# Beamer Visual Asset

## Rules
- Keep real slide text in TeX, not inside generated images.
- Store deck-specific figures in the deck case `assets/figures/`.
- Store template-level logos or reusable visual assets in the template source case.
- Use trusted local or official assets for institution logos.
- Prefer vector or high-resolution images when the output is PDF.

## Checks
- Confirm every `\includegraphics{...}` path resolves after template/deck overlay.
- Confirm images are not cropped unintentionally in rendered previews.
- Confirm logos are not stretched or placed over navigation/footer elements.
