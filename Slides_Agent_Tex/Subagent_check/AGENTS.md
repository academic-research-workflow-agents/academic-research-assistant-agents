# Subagent_check Contract

## Role
`Subagent_check` owns all checks and tests.

It is responsible for:

- path and manifest checks
- source contract checks
- template smoke compilation
- deck compilation
- LaTeX log diagnostics
- PDF and PNG preview checks
- root hygiene checks

It is not responsible for:

- editing slide narrative as its main function
- editing authoritative template source as its main function
- becoming a second root

## Case Architecture
Check work lives under:

```text
examples/<slide_case>/<child_case>/
```

Check outputs belong inside that check case or inside the active checked case `outputs/` directory.
