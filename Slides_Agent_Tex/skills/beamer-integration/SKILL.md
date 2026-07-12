---
name: beamer-integration
description: Coordinate Beamer deck cases with template source cases. Use when Codex needs to map which deck uses which template, define template-copy and deck-overlay flow, maintain integration manifests, or decide build readiness across template, deck, and check layers.
---

# Beamer Integration

## Workflow
1. Locate the integration case under `Subagent_integrate/examples/<slide_case>/<child_case>/`.
2. Read the deck case manifest and template case manifest.
3. Ensure the selected template source case is smoke-compilable.
4. Ensure the deck case can be overlaid into a template worktree.
5. Route implementation work back to the owning subagent:
   - template styling -> `Subagent_template`
   - slide content -> `Subagent_deck`
   - diagnostics -> `Subagent_check`

## Manifest Rules
- Use workspace-relative paths.
- Do not hard-code machine-specific absolute paths.
- Do not store authoritative template source or deck source in the integration case.
