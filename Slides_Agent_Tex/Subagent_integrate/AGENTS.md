# Subagent_integrate Contract

## Role
`Subagent_integrate` coordinates deck and template cases.

It is responsible for:

- mapping each deck case to its template source case
- tracking build readiness across cases
- defining template-copy and deck-overlay flow
- preserving cross-case coordination manifests

It is not responsible for:

- writing slide content
- modifying template styling details
- running every diagnostic itself

## Case Architecture
Integration work lives under:

```text
examples/<slide_case>/<child_case>/
```

The integration case may reference template and deck cases by workspace-relative paths.

Do not store source decks or authoritative template trees here.
