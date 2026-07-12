---
name: beamer-check
description: Run source, compile, log, PDF, and PNG checks for Beamer template and deck cases. Use when Codex needs diagnostics, smoke compilation, render validation, missing resource checks, root hygiene checks, or LaTeX warning analysis.
---

# Beamer Check

## Workflow
1. Identify the active child case.
2. Run source checks before rendering.
3. Compile through `npm run render`.
4. Inspect logs for fatal errors, missing files, undefined citations, undefined references, and large overfull boxes.
5. Generate PNG previews when visual inspection is needed.

## Commands
```powershell
npm run inspect -- --case <child-case>
npm run check-source -- --case <child-case>
npm run render -- --case <child-case>
npm run render:png -- --case <child-case>
```

## Render Issues To Surface
- title or body overflow
- clipped figures
- low contrast
- logo collision
- footer or navigation overlap
- missing citations or bibliography failures
