from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = SUBAGENT_ROOT / "examples"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def source_manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "source_manifest.json"


def load_manifest(case_root: Path) -> dict[str, Any]:
    manifest = read_json(source_manifest_path(case_root))
    if manifest.get("content_mode") != "layout_only":
        raise ValueError("source_manifest.content_mode must be 'layout_only'.")
    if manifest.get("research_case") != case_root.parent.name:
        raise ValueError("source_manifest.research_case must match the outer case directory.")
    if manifest.get("case_id") != case_root.name:
        raise ValueError("source_manifest.case_id must match the child case directory.")
    return manifest


def resolve_declared_path(case_root: Path, relative_path: str, allowed_roots: tuple[str, ...]) -> Path:
    candidate = (case_root / relative_path).resolve()
    allowed = [(case_root / root).resolve() for root in allowed_roots]
    if not any(candidate == root or root in candidate.parents for root in allowed):
        raise ValueError(f"Declared path escapes allowed roots {allowed_roots}: {relative_path}")
    return candidate


def safe_output_path(case_root: Path, relative_path: str, output_group: str) -> Path:
    root = (case_root / "outputs" / "build" / output_group).resolve()
    target = (root / relative_path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Output target escapes its build root: {relative_path}")
    return target


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_case_skeleton(case_root: Path) -> None:
    for relative in ("inputs", "assets", "manifests", "outputs"):
        (case_root / relative).mkdir(parents=True, exist_ok=True)


def default_manifest(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "case_id": case_root.name,
        "content_mode": "layout_only",
        "entrypoint": None,
        "sources": [],
        "assets": [],
    }
