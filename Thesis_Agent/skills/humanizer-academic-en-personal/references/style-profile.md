# Personal Style Profile (English)

This profile is derived from the user's full English paper, with extra weight on methods, variable construction, regression interpretation, robustness, and conclusion sections. Use it to emulate structure and writing rhythm, not to copy wording.

## Core Traits To Preserve

- Section purpose is usually made explicit early.
- A sentence usually does one main job: define first, then add the necessary fact, without an extra layer of self-justification.
- English sentences should keep normal prose spacing and rhythm even inside LaTeX source; do not let formula habits or Chinese spacing habits spill into ordinary prose.
- Empirical writing often proceeds from definition to construction to interpretation.
- Results paragraphs commonly follow this order:
  1. state the sign or significance
  2. translate the magnitude
  3. connect the result to a mechanism or hypothesis
  4. add a bounded interpretation
- Discussion and conclusion sections stay argument-driven rather than rhetorical.

## Section-Level Habits

### Variables, Data, And Model

Preferred moves:
- Introduce the object first: variable, proxy, data source, sample restriction, or model choice.
- State the data layer that is actually used in the current construction.
- Explain the construction or necessary handling rule.
- Then explain why that choice helps identification or reduces a specific concern.

Useful sentence patterns to preserve in spirit:
- "X is used as the proxy for ..."
- "This paper uses ..."
- "According to ..."
- "To mitigate the endogeneity problem ..."

Preferred revision:
- Keep the structure above, but smooth the English into idiomatic academic prose.
- Open with the research object, proxy, or verified definition rather than with the database or processing pipeline.
- Do not bring in unused data layers just for completeness.
- Convert implementation detail into paper language instead of naming scripts, files, or pipeline outputs.
- Define the variable in terms of what it measures, not by saying what it is "not."
- Prefer shorter and plainer sentences over over-explained academic padding.
- In LaTeX prose, keep identifiers readable but not intrusive: reserve `\texttt{}` for genuine identifiers, keep ordinary numbers in ordinary text, and move equations into math mode instead of treating whole formulas as monospaced strings.
- If the user has already compressed a sentence into a more natural rhythm, patch the missing fact instead of rebuilding the whole sentence.
- Keep vendor-defined screening criteria short in the main prose and move the full rule set to appendix-style notes.
- Treat project-defined city codings and constructed measures as constructed objects: explain the analytical definition in the main text, and reserve exact code lists, overrides, and exceptions for notes.
- Replace vague nouns with defined objects or move them to a clearly named note.
- If cross-case harmonization is not yet complete, write only what the current asset can support.
- Avoid explanatory filler such as "these fields are sufficient," "this choice ensures," or "it should also be noted" unless the explanation itself carries analytical weight.

### Regression Interpretation

Preferred moves:
- Report the main coefficient first.
- Translate it into economic magnitude when the source allows, often relative to the sample mean or benchmark.
- Then explain why the result is consistent with a mechanism or hypothesis.

Useful sentence patterns to preserve in spirit:
- "The results show ..."
- "Column (1) indicates ..."
- "An increase of one standard deviation ..."
- "This is consistent with Hypothesis ..."

Preferred revision:
- Keep the disciplined order, but avoid repetitive sentence openings.

### Robustness And Extended Analysis

Preferred moves:
- Name the substitution or extension clearly.
- State how the sign, magnitude, or significance changes.
- Use restrained language when the result weakens.

### Conclusion And Implications

Preferred moves:
- Summarize the main findings compactly.
- State implications with limits.
- Keep policy implications narrower than the broadest possible claim.

## Habits To Correct

- Reduce repeated stacks of "may", "might", and "could" in the same sentence or paragraph.
- Prefer idiomatic phrases such as "is measured by", "is defined as", "is associated with", and "consistent with".
- Avoid thesis-proposal language when writing a finished paper.
- Avoid literal Chinese-to-English structures such as "the influence can be divided into two aspects" when a more natural formulation is available.
- Do not preserve awkward wording only for the sake of sounding like the source.

## Front-Matter Overlay (Additive, Not Replacing)

These rules come from the 46-paper front-matter reading pass. Use them as an overlay for abstracts, introductions, conclusions, and keywords; keep the existing methods, data, regression, and robustness profile intact.

### Abstract

- Use the order question or object -> data and identification -> main result -> one mechanism or heterogeneity layer -> bounded implication.
- Allow at most one short background sentence before the paper's exact task appears.
- Let the confirmed Chinese abstract anchor the English structure when both versions are being drafted.

### Introduction

- Keep the opening context to 1-2 sentences before moving to the research question.
- A stable order is short context -> research question -> literature gap -> design preview -> contribution bundle.
- Contribution points should map directly to design, sample, mechanism, or comparison rather than to broad claims about significance.

### Conclusion And Implications

- Recap the main finding first, then the most decision-relevant mechanism, heterogeneity, or extension result, and only then add a bounded implication or boundary statement.
- Do not replay every table if the paper has many mechanism and heterogeneity exercises.
- If limitations are mentioned, use them to delimit scope rather than to open a generic future-research wish list.

### Keywords

- Keep the keyword set small and stable, usually `3-6` items and often `4` for the current thesis.
- Prefer the order topic -> object or setting -> method, with at most one method term and only when the method is truly central to the paper's identity.
- Use one delimiter system, usually commas or semicolons, and avoid sentence-like phrases.

### Drafting Order

- Draft thesis front matter serially rather than in parallel: Chinese conclusion -> English conclusion -> Chinese introduction -> English introduction -> Chinese abstract -> English abstract -> Chinese keywords -> English keywords.
- Let confirmed Chinese structure anchor the English version; absorb the functional moves of English papers without letting English reorder the accepted Chinese logic.

## What Not To Copy

- Do not copy formatting conventions, headings, citation style, or sentence-level phrasing.
- Do not preserve immature hedging or translation artifacts.
- Do not inherit weak policy overreach if the evidence does not support it.
