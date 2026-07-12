---
name: humanizer-academic-en
description: >
  Rewrite English literature reviews and related academic prose to remove
  generic AI writing patterns while preserving claims, evidence, disagreements,
  variables, models, and causal boundaries. Use for literature reviews,
  mechanism discussion, variable definitions, regression interpretation, and
  robustness checks. Do not impose formatting or invent citations.
---

# Academic Humanizer (English)

Use this skill to revise English academic prose that sounds padded, formulaic, or obviously AI-generated. Keep the argument, evidence, literature disagreement, notation, and disciplinary register intact.

Read only the files you need:

- `references/section-playbook.md`
- `references/anti-patterns.md`

## Workflow

1. Identify the section you are revising and preserve that section's job.
2. Remove filler, inflated framing, vague attribution, and generic academic boilerplate.
3. Keep variables, equations, comparisons, disagreements, and causal boundaries unchanged unless the user asks for substantive editing.
4. Prefer precise academic prose over chatty "human voice".
5. Return the revised text only, unless the user asks for comments.

## Hard Rules

- Do not invent data, citations, variables, models, coefficients, sample periods, mechanisms, or policy implications.
- Do not impose thesis or journal formatting unless the user explicitly requests it.
- Do not turn academic prose into marketing copy, blog prose, or chatbot correspondence.
- Do not weaken definitions, disagreements, or identification logic just to sound less AI-like.
- Keep necessary caution when the evidence is limited, but remove stacked hedging and empty softeners.
- Literature reviews must stay in literature-review voice rather than drifting into introduction voice or conclusion voice.

## Output

Default output:

- Revised text only
