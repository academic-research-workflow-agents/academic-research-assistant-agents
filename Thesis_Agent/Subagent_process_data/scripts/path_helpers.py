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


def get_case_scripts_root(start: Path, case_name: str, thesis_name: str | None = None) -> Path:
    return resolve_case_root(start, case_name, thesis_name=thesis_name) / "scripts"


def get_thesis_root(start: Path, thesis_name: str | None = None) -> Path:
    examples_root = get_examples_root(start)
    if thesis_name is not None:
        thesis_root = examples_root / thesis_name
        if thesis_root.exists():
            return thesis_root
        raise FileNotFoundError(f"Unable to resolve thesis case {thesis_name!r} under {examples_root}")
    current = start.resolve()
    for candidate in (current, *current.parents):
        if candidate.parent == examples_root:
            return candidate
    return get_examples_root(start)


def resolve_case_root(start: Path, case_name: str, thesis_name: str | None = None) -> Path:
    examples_root = get_examples_root(start)
    thesis_root = get_thesis_root(start, thesis_name=thesis_name)
    if thesis_root != examples_root:
        nested = thesis_root / case_name
        if nested.exists():
            return nested
    elif thesis_name is not None:
        nested = examples_root / thesis_name / case_name
        if nested.exists():
            return nested
    flat = examples_root / case_name
    if flat.exists():
        return flat
    if thesis_name is not None:
        return examples_root / thesis_name / case_name
    if thesis_root != examples_root:
        return thesis_root / case_name
    return flat

