---
name: humanizer-academic-en
description: >
  Rewrite English academic prose to remove generic AI writing patterns while
  preserving claims, evidence, variables, models, and causal boundaries. Use
  for journal-style papers, theses, abstracts, introductions, keywords,
  literature reviews, methods sections, regression interpretation, robustness
  checks, and conclusions. Do not impose formatting or invent citations.
---

# Academic Humanizer (English)

Use this skill to revise English academic prose that sounds padded, formulaic, or obviously AI-generated. Keep the argument, evidence, notation, and disciplinary register intact.

Read only the files you need:
- `references/section-playbook.md` for section-specific guidance
- `references/anti-patterns.md` for rewrite targets

## Workflow

1. Identify the section you are revising and preserve that section's job; for abstracts, introductions, keywords, and conclusions, layer the front-matter supplement in `section-playbook` onto the existing template logic rather than replacing the original section rules.
2. Remove academic filler, inflated framing, vague attribution, and generic AI conclusions.
3. Keep variables, equations, coefficients, table references, sample definitions, and causal boundaries unchanged unless the user asks for substantive editing.
4. Prefer precise academic prose over chatty "human voice".
5. Return the revised text only, unless the user asks for comments or a diagnosis.

## Hard Rules

- Do not invent data, citations, variables, models, coefficients, sample periods, mechanisms, or policy implications.
- Do not impose university, thesis, or journal formatting unless the user explicitly requests it.
- Do not turn academic prose into marketing copy, blog prose, or chatbot correspondence.
- Do not weaken definitions or identification logic just to sound less AI-like.
- Keep necessary caution when the evidence is limited, but remove stacked hedging and empty softeners.
- Preserve equation labels, table labels, and domain-specific terminology.

## Routing

- Abstract, introduction, keywords, literature review, mechanism or hypothesis sections: read `references/section-playbook.md`
- Variable description, data, empirical model, regression interpretation, robustness, conclusion: read `references/section-playbook.md`
- If the text sounds generic, ceremonial, vague, or over-hedged: read `references/anti-patterns.md`

## Output

Default output:
- Revised text only

Optional output when requested:
- A short note on the main issues removed
