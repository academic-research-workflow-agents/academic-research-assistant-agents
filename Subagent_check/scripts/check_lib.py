from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SUBAGENT_ROOT.parent
EXAMPLES_ROOT = SUBAGENT_ROOT / "examples"


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


def resolve_existing_case_root() -> Path:
    env_case_root = os.environ.get("CHECK_CASE_ROOT")
    if env_case_root:
        candidate = Path(env_case_root).resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"CHECK_CASE_ROOT does not exist: {candidate}")
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if candidate.parent.parent == EXAMPLES_ROOT:
            return candidate
    raise RuntimeError("Set CHECK_CASE_ROOT or run from examples/<research_case>/<child_case>.")


def manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "research_check_manifest.json"


def report_json_path(case_root: Path) -> Path:
    return case_root / "outputs" / "research_check_report.json"


def report_md_path(case_root: Path) -> Path:
    return case_root / "outputs" / "research_check_report.md"


def ensure_case_skeleton(case_root: Path) -> None:
    for name in ("manifests", "requests", "outputs", "scripts"):
        (case_root / name).mkdir(parents=True, exist_ok=True)


def default_case_agents(case_name: str) -> str:
    return f"# {case_name}\n\nThis check case validates linked paths and manifests without editing target cases.\n"


def default_case_readme(case_name: str) -> str:
    return f"# {case_name}\n\nSet `coordination_case_ref`, then run `run_research_check.py`.\n"


def default_check_manifest(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "coordination_case_ref": "",
        "check_scope": {"linked_cases": True},
        "focus_targets": [],
        "check_tracks": [{"track_name": "paths_and_manifests"}],
        "scan_policy": {"read_only": True},
        "report_preferences": {"markdown": True, "json": True},
        "last_resolved_target_refs": [],
    }


def resolve_workspace_path(case_root: Path, reference: str) -> Path:
    candidate = (case_root / reference).resolve()
    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ValueError(f"Reference escapes the workspace: {reference}")
    return candidate


def target_selected(target: dict[str, Any], selectors: list[dict[str, Any]]) -> bool:
    if not selectors:
        return True
    for selector in selectors:
        if selector.get("capability") and selector["capability"] == target.get("capability"):
            return True
        if selector.get("subagent") and selector["subagent"] == target.get("subagent"):
            return True
        if selector.get("case_ref") and selector["case_ref"] == target.get("relative_path"):
            return True
    return False


def run_check(case_root: Path) -> dict[str, Any]:
    manifest = read_json(manifest_path(case_root))
    if not isinstance(manifest, dict):
        raise FileNotFoundError(f"Missing check manifest: {manifest_path(case_root)}")
    issues: list[dict[str, str]] = []
    if manifest.get("research_case") != case_root.parent.name:
        issues.append({"severity": "error", "message": "research_case does not match the case namespace."})
    coordination_ref = str(manifest.get("coordination_case_ref") or "")
    coordination_manifest: dict[str, Any] = {}
    if not coordination_ref:
        issues.append({"severity": "error", "message": "coordination_case_ref is required."})
    else:
        coordination_path = resolve_workspace_path(case_root, coordination_ref)
        if coordination_path.is_dir():
            coordination_path = coordination_path / "manifests" / "research_coordination_manifest.json"
        coordination_manifest = read_json(coordination_path, {}) or {}
        if not coordination_manifest:
            issues.append({"severity": "error", "message": f"Coordination manifest not found: {coordination_ref}"})
        elif coordination_manifest.get("research_case") != manifest.get("research_case"):
            issues.append({"severity": "error", "message": "Coordination manifest uses a different research_case."})
    selectors = list(manifest.get("focus_targets") or [])
    snapshots: list[dict[str, Any]] = []
    for target in coordination_manifest.get("linked_cases") or []:
        if not target_selected(target, selectors):
            continue
        reference = str(target.get("relative_path") or "")
        resolved = resolve_workspace_path(case_root, reference)
        present = resolved.is_dir()
        snapshots.append({**target, "resolved": str(resolved), "present": present})
        if not present:
            issues.append({"severity": "error", "message": f"Linked case is missing: {reference}"})
    updated_manifest = dict(manifest)
    updated_manifest["last_resolved_target_refs"] = [item["relative_path"] for item in snapshots]
    return {
        "schema_version": 1,
        "research_case": manifest.get("research_case"),
        "status": "fail" if any(item["severity"] == "error" for item in issues) else "pass",
        "issues": issues,
        "target_snapshot": snapshots,
        "checked_at": utc_now_iso(),
        "updated_check_manifest": updated_manifest,
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Research Check Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Research case: `{report.get('research_case', '')}`",
        "",
        "## Issues",
        "",
    ]
    lines.extend(f"- {item['severity']}: {item['message']}" for item in report["issues"] or [{"severity": "info", "message": "No issue."}])
    lines.extend(["", "## Targets", ""])
    lines.extend(f"- `{item['relative_path']}`: `{item['present']}`" for item in report["target_snapshot"] or [])
    lines.append("")
    return "\n".join(lines)
