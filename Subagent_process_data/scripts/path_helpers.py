from __future__ import annotations

from pathlib import Path


def find_named_ancestor(start: Path, target_name: str) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if candidate.name == target_name:
            return candidate
    raise FileNotFoundError(f"Unable to find ancestor named {target_name!r} from {start}")


def get_subagent_root(start: Path) -> Path:
    return find_named_ancestor(start, "Subagent_process_data")


def get_subagent_scripts_root(start: Path) -> Path:
    return get_subagent_root(start) / "scripts"


def get_workspace_root(start: Path) -> Path:
    return get_subagent_root(start).parent


def get_examples_root(start: Path) -> Path:
    return get_subagent_root(start) / "examples"


def get_data_panel_scripts_root(start: Path) -> Path:
    return get_subagent_root(start) / "skills" / "Codex-data_panel" / "scripts"


def get_case_scripts_root(start: Path, case_name: str, research_name: str | None = None) -> Path:
    return resolve_case_root(start, case_name, research_name=research_name) / "scripts"


def get_research_root(start: Path, research_name: str | None = None) -> Path:
    examples_root = get_examples_root(start)
    if research_name is not None:
        research_root = examples_root / research_name
        if research_root.exists():
            return research_root
        raise FileNotFoundError(f"Unable to resolve research case {research_name!r} under {examples_root}")
    current = start.resolve()
    for candidate in (current, *current.parents):
        if candidate.parent == examples_root:
            return candidate
    return get_examples_root(start)


def resolve_case_root(start: Path, case_name: str, research_name: str | None = None) -> Path:
    examples_root = get_examples_root(start)
    research_root = get_research_root(start, research_name=research_name)
    if research_root != examples_root:
        nested = research_root / case_name
        if nested.exists():
            return nested
    elif research_name is not None:
        nested = examples_root / research_name / case_name
        if nested.exists():
            return nested
    flat = examples_root / case_name
    if flat.exists():
        return flat
    if research_name is not None:
        return examples_root / research_name / case_name
    if research_root != examples_root:
        return research_root / case_name
    return flat
