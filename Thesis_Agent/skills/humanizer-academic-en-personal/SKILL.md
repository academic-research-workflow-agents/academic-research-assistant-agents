---
name: humanizer-academic-en-personal
description: >
  Rewrite English academic prose in a cleaner economics-and-finance empirical
  style while preserving claims, evidence, variables, models, and causal
  boundaries. Use for abstracts, introductions, keywords, literature reviews,
  hypotheses, variable definitions, empirical models, regression interpretation,
  robustness checks, and conclusions. Do not impose formatting or invent citations.
---

# Academic Humanizer (English, Personal)

Use this skill to revise English academic prose for economics and finance empirical writing. The default academic rules still apply, but when the task fits empirical paper writing, also use the personal style profile to emulate the author's section-level habits without copying phrasing or formatting.

Read only the files you need:
- `references/section-playbook.md` for section-specific guidance
- `references/anti-patterns.md` for rewrite targets
- `references/style-profile.md` when the task is economics or finance empirical writing, or when the user wants the text to sound closer to their own paper voice

## Workflow

1. Identify the section you are revising and preserve that section's job; for abstracts, introductions, keywords, and conclusions, apply the front-matter supplement in `section-playbook` and `style-profile` as an additive layer rather than a replacement for the existing personal style rules.
2. If the user has manually revised the Chinese draft, treat that draft as the primary structural anchor and default to patching rather than rewriting.
3. Remove academic filler, inflated framing, vague attribution, and generic AI conclusions.
4. Keep variables, equations, coefficients, sample definitions, and causal boundaries unchanged unless the user asks for substantive editing.
5. When the task fits an economics or finance empirical paper, apply the personal style profile at the level of structure, rhythm, and result interpretation; in front-matter tasks, treat the new supplement as an addition to the existing profile rather than an override.
6. Correct awkward or over-hedged English even when that means departing from the source sentence.
7. Return the revised text only, unless the user asks for comments or a diagnosis.

## Hard Rules

- Do not invent data, citations, variables, models, coefficients, sample periods, mechanisms, or policy implications.
- Do not imitate thesis or journal formatting.
- Do not copy the author's original sentences.
- Do not preserve non-idiomatic English just because it appears in the source paper.
- Keep the author's empirical writing logic, but prefer mature academic English over literal translation.
- The latest manually revised Chinese draft outranks any earlier assistant draft; unless there is a factual problem, do not rewrite a sentence the user has already compressed well.
- When the user manually revises Chinese first, archive that Chinese draft before any assistant rewrite and follow it as the primary structural anchor.
- In methods, variables, and sample sections, discuss only the data layers that actually enter the current construction.
- Translate technical processing into paper language rather than exposing script names, file names, output paths, or pipeline order.
- Define variables positively in terms of what they measure; do not rely on contrastive phrases such as "rather than" to do the conceptual work.
- Summarize vendor-defined screening rules briefly in the main text, and place full criteria, keyword lists, or manual-style detail in appendix-style notes.
- For project-constructed variables or city definitions, keep the main text at the level of analytical construction and move exact code logic, overrides, and special cases to appendix-style notes.
- Do not preserve vague nouns such as "special rules," "standard cities," or "has" when the underlying definition is available and should be stated directly.
- Do not claim harmonization beyond what the current asset actually supports.
- Prefer established formal category names over assistant-invented umbrella terms.
- When a project-internal label first appears in the main text, introduce its source and what it refers to before relying on the label itself.
- If the user rejects only one detail, patch that detail instead of using it as an excuse to rewrite the whole sentence or paragraph.
- When the accepted Chinese draft is compact and readable, do not over-expand it into explanatory English just to make the sentence feel more symmetrical.

## Routing

- All section-specific revisions: read `references/section-playbook.md`
- Generic AI-shaped academic filler: read `references/anti-patterns.md`
- Economics or finance empirical style matching, or any abstract/introduction/keywords/conclusion task: read `references/style-profile.md`

## Output

Default output:
- Revised text only

Optional output when requested:
- A short note on the main issues removed or the style choices applied
