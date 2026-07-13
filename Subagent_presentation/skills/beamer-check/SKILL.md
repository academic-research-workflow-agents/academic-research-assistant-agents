---
name: beamer-check
description: Validate provenance, source paths, compilation, logs, PDF output, and PNG previews for Beamer presentation cases. Use when Codex must diagnose missing sources, frame-label mismatches, missing assets, LaTeX failures, or visual layout defects.
---

# Beamer Check

1. Run the provenance and source check first.
2. Compile only after every frame is registered and source-bound.
3. Inspect logs for fatal errors, missing files, undefined citations, undefined references, and large overfull boxes.
4. Export PNG previews when visual inspection is needed.

```powershell
npm run presentation:inspect -- --case <child-case>
npm run presentation:check-source -- --case <child-case>
npm run presentation:render -- --case <child-case>
npm run presentation:render:png -- --case <child-case>
```
