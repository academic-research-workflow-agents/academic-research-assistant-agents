---
name: skill-creator
description: Guide for creating effective skills. Use when Codex needs to create a new skill or update an existing skill with specialized instructions, reusable workflows, scripts, references, or assets.
license: Complete terms in LICENSE.txt
---

# Skill Creator

Create or update a skill that another Codex instance can use reliably.

## Core Principles

- Keep the context budget lean. Add only the guidance Codex is unlikely to infer on its own.
- Put trigger conditions in frontmatter `description`, not in a separate "when to use" section.
- Prefer reusable resources over repeating the same code or reference material in every task.
- Match instruction precision to task fragility. Use guardrails when consistency matters.

## Skill Anatomy

Each skill must include:

- `SKILL.md`
  - YAML frontmatter with `name` and `description`
  - Markdown instructions that explain how to use the skill

Optional bundled resources:

- `scripts/` for deterministic helpers or repeated automation
- `references/` for supporting documentation loaded only when needed
- `assets/` for templates or files used in outputs instead of context

Do not add extra project-style documents such as `README.md`, `CHANGELOG.md`, or installation guides unless a user explicitly requires them.

## Creation Workflow

Follow this sequence unless there is a clear reason to skip a step:

1. Understand the target skill with concrete examples and trigger phrases.
2. Decide which reusable resources belong in `scripts/`, `references/`, or `assets/`.
3. Initialize the skill with `scripts/init_skill.py <skill-name> --path <output-directory>`.
4. Replace template content with real instructions and only the resources that are needed.
5. Validate the skill with `scripts/quick_validate.py <path/to/skill-folder>`.
6. Iterate after real use.

## Design Guidance

### Frontmatter

- Keep `name` in lowercase hyphen-case.
- Make `description` state both capability and trigger conditions.
- Keep the frontmatter aligned with the folder name.

### Body

- Write in imperative form.
- Prefer short workflows, decision rules, and concrete examples over long narrative explanation.
- Move large details into `references/` and link them from `SKILL.md`.
- Remove placeholders before considering the skill complete.

### Resources

- Add scripts only when a repeated or fragile operation benefits from automation.
- Add references only when they provide reusable knowledge that should not bloat `SKILL.md`.
- Add assets only when the skill genuinely needs files to copy or consume during output generation.

## Reusable Guides

- Read `references/workflows.md` when the skill needs a clear sequential or branching workflow.
- Read `references/output-patterns.md` when the skill needs output templates or quality patterns.

## Validation

Run:

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

Fix validation issues before handing the skill back.

## Iteration

Improve the skill after real use:

1. Notice where Codex struggled or repeated work.
2. Update instructions or bundled resources to remove that friction.
3. Re-run validation.
