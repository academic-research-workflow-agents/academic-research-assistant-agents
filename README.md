# Academic Research Workflow Agents

中文名：学术研究工作流智能体框架

This private paid-source monorepo contains two reusable agent frameworks for academic research work:

- `Thesis_Agent/`: a thesis workflow framework covering paper reading, data preparation, Stata regression work, LaTeX writing, integration, and submission checks.
- `Slides_Agent_Tex/`: a TeX/Beamer-first slide authoring framework for academic presentations.

The repository is intended to store generic framework code, contracts, skills, scripts, and synthetic examples only. Real papers, private datasets, generated outputs, logs, institution-specific templates, and archived runs should stay in private working directories outside this repository.

## Repository Layout

```text
Thesis_Agent/
Slides_Agent_Tex/
```

Each subproject has its own `README.md` and `AGENTS.md` with routing rules and project-specific contracts.

## Visibility

This repository is private by default and is the source for paid release packages. Do not make this repository public.

For public evaluation material, use the separate preview repository:

```text
academic-research-workflow-agents/agents-preview
```

## Paid Release Packages

Release packages are distributed as versioned ZIP archives after purchase through Chinese payment or marketplace channels such as Xianyu.

```powershell
.\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0
```

The script creates:

- `Academic_Research_Workflow_Agents_v<version>.zip`
- `Academic_Research_Workflow_Agents_v<version>.zip.sha256.txt`

Release archives are for personal use only. See `TERMS.md`.
