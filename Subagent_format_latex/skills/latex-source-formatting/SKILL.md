---
name: latex-source-formatting
description: Mechanically convert and arrange user-provided Markdown, LaTeX, tables, figures, and bibliography assets. Use when Codex must preserve supplied academic text while applying LaTeX layout or compiling a technical preview.
---

# LaTeX Source Formatting

1. Work inside `Subagent_format_latex/examples/<research_case>/<child_case>/`.
2. Require every input in `manifests/source_manifest.json`.
3. Preserve explicit LaTeX sources byte-for-byte and use Pandoc only for declared Markdown conversion.
4. Record input hashes and converter metadata in runtime reports.
5. Stop when source text is missing. Do not add正文, claims, explanations, findings, or conclusions.
