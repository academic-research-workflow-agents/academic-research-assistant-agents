# Section Playbook

Use the subsection that matches the user's current task.
The front-matter supplement below is additive. Use it with the existing empirical-writing rules rather than as a replacement.

## Abstract

Goal:
- State the question, sample, method, main result, and bounded contribution.

Rewrite priorities:
- Remove ceremony and vague significance claims.
- Keep the empirical design and the core findings concrete.
- Preserve caution where the design requires it.
- As a supplemental order, move through object or question -> data and identification -> main result -> one necessary mechanism or heterogeneity layer -> bounded implication.
- Allow at most one short background sentence before landing on the paper's exact task.
- When a bilingual abstract is being written, treat the confirmed Chinese abstract as the structural anchor for the English version rather than letting English reshape the Chinese order.

## Introduction

Goal:
- Define the problem, show the gap, and state the paper's contribution cleanly.

Rewrite priorities:
- Move quickly from context to the exact research problem.
- Replace broad framing with specific institutional or empirical motivation.
- Keep contribution claims narrow and evidence-linked.
- As a supplemental order, prefer 1-2 sentences of context -> research question -> literature gap -> design preview -> contribution bundle.
- Do not let the front of the introduction dissolve into a mini literature review before the question and design appear.
- Method-paper compression can inform tone, but it should not displace the thesis introduction's empirical problem-first structure.

## Literature Review

Goal:
- Position the paper within the literature by strand, disagreement, mechanism, or setting.

Rewrite priorities:
- Prefer synthesis over author-by-author narration.
- Keep disagreements and unresolved findings visible.
- Avoid generic claims about what "the literature" says unless the text already supports them.

## Mechanism And Hypotheses

Goal:
- Explain the mechanism, then state the testable prediction.

Rewrite priorities:
- Define the channel before naming the hypothesis.
- Keep hypotheses directional and tied to the mechanism.
- Avoid padded transitions and theatrical buildup.

## Variables, Data, And Empirical Model

Goal:
- Define the variable or sample first, then explain construction, source, and identification logic.

Rewrite priorities:
- State the object first, then the data source actually used, then the construction or necessary handling rule.
- If the user has manually revised the paragraph in Chinese, preserve its sentence skeleton and paragraph order unless a factual fix forces a structural change.
- If the user rejects only one detail, patch that detail rather than rewriting the entire sentence or paragraph.
- Do not introduce unused data layers, backup sources, or validation materials into the main prose.
- Convert technical processing into paper language rather than naming scripts, file names, output paths, or step-by-step pipeline order.
- Define variables positively in terms of what they measure; avoid contrastive definitions built around "rather than."
- Keep the main text brief and readable; move full screening criteria, keyword lists, code inventories, and exception handling to appendix-style notes.
- When a project-internal label first appears, state its source and referent in the same paragraph instead of sending the reader to the appendix immediately.
- Prefer formal category names plus exact numbers over assistant-invented umbrella terms.
- In direct_latex mode, long supplementary material should usually become an appendix rather than another subsection inside the main chapter. In the main text, point readers there directly, for example with “see Appendix A,” instead of burying the material in a long footnote.
- If subsections become too dense and each block is short, merge them back into natural paragraphs instead of letting the chapter read like an outline or a technical memo.
- When the data object is project-constructed rather than publicly packaged, say how it is constructed without pretending it is an off-the-shelf dataset.
- Internal table IDs, field names, and script-side identifiers should stay out of the main prose unless the user explicitly wants them or the paragraph truly needs them.
- Ordinary numbers, years, sample sizes, thresholds, and code values should not be wrapped in `\texttt{}`. Reserve `\texttt{}` for identifiers such as variable names, field names, and file names. If a formula contains numbers, prefer math mode instead of monospacing the numbers.
- In English prose, keep normal word spacing around numbers and units: `342 city units`, `USD 1 million`, `in 2024`. Do not import Chinese no-space habits into English sentences.
- Keep normal prose spacing around inline identifiers as well: write `the variable \texttt{ai_level} is defined as ...`, not a glued form such as `variable\texttt{ai_level}`.
- Separate prose from equations cleanly. Use math mode for formulas, and let the surrounding sentence read like ordinary English.
- Replace vague nouns with defined objects. If the prose would become too heavy, keep the short version in the main text and define the object in a note.
- Avoid trailing explanatory filler such as "these fields are sufficient" or "this choice ensures" unless the sentence would otherwise lose analytical content.
- If the accepted Chinese draft is compact, keep the English equally compact; do not add explanatory symmetry that the source does not need.
- Preserve notation, lag structure, fixed effects, clustering, winsorization, and data-source details.
- Prefer "is measured by", "is defined as", "is constructed from", and similarly direct academic phrasing.
- Keep operational detail exact.

## Regression Interpretation

Goal:
- Report sign, significance, magnitude, and economic meaning in a controlled order.

Rewrite priorities:
- Report the result first.
- Translate the magnitude next, often relative to a mean or benchmark when the source does so.
- Then connect the finding to the mechanism or hypothesis.
- Do not overclaim.

## Robustness Checks

Goal:
- Explain what was replaced or added, and whether the core finding remains.

Rewrite priorities:
- Name the robustness exercise clearly.
- Distinguish unchanged, weaker, and mixed evidence.
- Keep the tone measured.

## Conclusion And Implications

Goal:
- Summarize the main findings and provide limited implications.

Rewrite priorities:
- Tie implications to the evidence.
- Avoid broad policy slogans or generic social significance.
- End with a bounded takeaway.
- As a supplemental order, recap the main result first, then the key mechanism or extension, and only then add a bounded implication or boundary statement.
- If the main text already contains mechanism and heterogeneity evidence, recall only the most decision-relevant layer instead of replaying every table.
- If limitations are mentioned, use them to clarify scope rather than to open a generic future-research list.

## Keywords

Goal:
- Use a small, stable keyword set that covers the topic term, object or setting term, and only when needed a method term.

Rewrite priorities:
- Revise only author-supplied keywords; do not invent new ones from the theme.
- English keyword sets usually work best with `3-6` items, often `4`, ordered as topic -> object or setting -> method when method is central.
- Use one stable delimiter, usually commas or semicolons, and avoid sentence fragments or mixed-language baskets.
