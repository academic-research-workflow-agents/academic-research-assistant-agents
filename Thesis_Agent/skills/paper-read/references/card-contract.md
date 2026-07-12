# Paper Card Contract

Each paper card should be saved as `cards/<citation_key>.md`.

Recommended structure:

```md
# <Paper Title>

- Citation Key: `<citation_key>`
- Reading Source: `<linked_bib|manual_pdf>`
- PDF Path Source: shared manifest or local manifest

## Research Question

## One-Sentence Takeaway

## Method / Identification

## Data And Sample

## Outcome Variable

## Core Explanatory Variable

## Controls

## Mechanisms / Heterogeneity

## Main Findings

## Limitations

## Reusable Writing Points

## Evidence Anchors
- p.X: ...
- p.Y: ...
```

Rules:
- Keep headings stable so later scripts and agents can scan them reliably.
- Keep evidence anchors specific enough that a user can audit them.
- When the paper does not report a field, say `Not explicitly stated` instead of guessing.
