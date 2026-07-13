from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SUBAGENT_ROOT.parent
EXAMPLES_ROOT = SUBAGENT_ROOT / "examples"
CAPABILITIES = [
    {"mode": "evidence", "subagent": "Subagent_evidence", "role": "evidence_base"},
    {"mode": "data_preparation", "subagent": "Subagent_process_data", "role": "data_assets"},
    {"mode": "empirical_analysis", "subagent": "Subagent_regress_stata", "role": "empirical_results"},
    {"mode": "document_formatting", "subagent": "Subagent_format_latex", "role": "layout_assets"},
    {"mode": "presentation", "subagent": "Subagent_presentation", "role": "presentation_assets"},
]
VALID_MODES = {item["mode"] for item in CAPABILITIES}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def relpath_from(base: Path, target: Path) -> str:
    return os.path.relpath(target, base).replace("\\", "/")


def resolve_existing_case_root() -> Path:
    env_case_root = os.environ.get("INTEGRATION_CASE_ROOT")
    if env_case_root:
        candidate = Path(env_case_root).resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"INTEGRATION_CASE_ROOT does not exist: {candidate}")
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if candidate.parent.parent == EXAMPLES_ROOT:
            return candidate
    raise RuntimeError("Set INTEGRATION_CASE_ROOT or run from examples/<research_case>/<child_case>.")


def manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "research_coordination_manifest.json"


def report_md_path(case_root: Path) -> Path:
    return case_root / "outputs" / "research_coordination_report.md"


def scan_json_path(case_root: Path) -> Path:
    return case_root / "outputs" / "research_coordination_scan.json"


def ensure_case_skeleton(case_root: Path) -> None:
    for name in ("manifests", "requests", "outputs", "scripts"):
        (case_root / name).mkdir(parents=True, exist_ok=True)


def default_case_agents(case_name: str) -> str:
    return f"""# {case_name}

This integration case records requested capabilities, linked child cases, blockers, and next actions. It does not edit linked cases or create academic正文.
"""


def default_case_readme(case_name: str) -> str:
    return f"""# {case_name}

Set `requested_capabilities` in `manifests/research_coordination_manifest.json`, then run `refresh_coordination_manifest.py`.
"""


def default_coordination_manifest(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "active_mode": "integration",
        "requested_capabilities": [],
        "linked_cases": [],
        "capability_status": {item["mode"]: "not_requested" for item in CAPABILITIES},
        "blockers": [],
        "next_actions": ["Declare the capabilities needed for this research case."],
        "updated_at": utc_now_iso(),
    }


def scan_business_cases(case_root: Path, research_case: str | None = None) -> list[dict[str, Any]]:
    research_name = research_case or case_root.parent.name
    linked_cases: list[dict[str, Any]] = []
    for item in CAPABILITIES:
        namespace = WORKSPACE_ROOT / item["subagent"] / "examples" / research_name
        if not namespace.exists():
            continue
        for child in sorted(path for path in namespace.iterdir() if path.is_dir()):
            linked_cases.append(
                {
                    "capability": item["mode"],
                    "subagent": item["subagent"],
                    "child_case": child.name,
                    "relative_path": relpath_from(case_root, child.resolve()),
                    "role": item["role"],
                    "status": "placeholder" if child.name.startswith("_") else "present",
                }
            )
    return linked_cases


def derive_capability_status(linked_cases: list[dict[str, Any]], requested: list[str]) -> dict[str, str]:
    status: dict[str, str] = {}
    for item in CAPABILITIES:
        mode = item["mode"]
        matches = [entry for entry in linked_cases if entry["capability"] == mode]
        if mode not in requested:
            status[mode] = "not_requested"
        elif any(entry["status"] == "present" for entry in matches):
            status[mode] = "ready"
        elif matches:
            status[mode] = "placeholder_only"
        else:
            status[mode] = "missing"
    return status


def build_coordination_manifest(case_root: Path) -> dict[str, Any]:
    existing = read_json(manifest_path(case_root), {}) or {}
    requested = list(dict.fromkeys(existing.get("requested_capabilities") or []))
    invalid = [mode for mode in requested if mode not in VALID_MODES]
    if invalid:
        raise ValueError(f"Unsupported requested capabilities: {invalid}")
    linked_cases = scan_business_cases(case_root)
    capability_status = derive_capability_status(linked_cases, requested)
    missing = [mode for mode in requested if capability_status[mode] != "ready"]
    blockers = [f"Requested capability is not ready: {mode}." for mode in missing]
    next_actions = [f"Create or select a {mode} child case under examples/{case_root.parent.name}/." for mode in missing]
    if not requested:
        next_actions = ["Declare the capabilities needed for this research case."]
    elif not missing:
        next_actions = ["All requested capabilities are linked; route the next action by user intent."]
    return {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "active_mode": missing[0] if missing else "integration",
        "requested_capabilities": requested,
        "linked_cases": linked_cases,
        "capability_status": capability_status,
        "blockers": blockers,
        "next_actions": next_actions,
        "updated_at": utc_now_iso(),
    }


def build_scan_payload(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "linked_cases": scan_business_cases(case_root),
        "scanned_at": utc_now_iso(),
    }


def build_coordination_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Research Coordination Report",
        "",
        f"- `research_case`: `{manifest['research_case']}`",
        f"- `active_mode`: `{manifest['active_mode']}`",
        "",
        "## Capability Status",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in manifest["capability_status"].items())
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in manifest["blockers"] or ["No blocker."])
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in manifest["next_actions"])
    lines.append("")
    return "\n".join(lines)
