from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from convert_sources_to_latex import convert_case  # noqa: E402


def write_manifest(case_root: Path, sources: list[dict]) -> None:
    (case_root / "manifests").mkdir(parents=True)
    payload = {
        "schema_version": 1,
        "research_case": case_root.parent.name,
        "case_id": case_root.name,
        "content_mode": "layout_only",
        "entrypoint": None,
        "sources": sources,
        "assets": [],
    }
    (case_root / "manifests" / "source_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_latex_source_is_copied_exactly_and_hashed(tmp_path: Path) -> None:
    case_root = tmp_path / "example_research" / "format_case"
    source = case_root / "inputs" / "section.tex"
    source.parent.mkdir(parents=True)
    supplied = "Exact user text with % and \\LaTeX{} syntax.\n"
    source.write_text(supplied, encoding="utf-8")
    write_manifest(case_root, [{"id": "section", "path": "inputs/section.tex", "format": "latex", "target": "section.tex"}])

    report = convert_case(case_root)
    output = case_root / "outputs" / "build" / "formatted" / "section.tex"

    assert output.read_bytes() == source.read_bytes()
    assert report["processed"][0]["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["processed"][0]["converter"] == "byte-copy"


def test_undeclared_source_is_not_processed(tmp_path: Path) -> None:
    case_root = tmp_path / "example_research" / "format_case"
    inputs = case_root / "inputs"
    inputs.mkdir(parents=True)
    (inputs / "declared.tex").write_text("Declared.\n", encoding="utf-8")
    (inputs / "undeclared.tex").write_text("Undeclared.\n", encoding="utf-8")
    write_manifest(case_root, [{"id": "declared", "path": "inputs/declared.tex", "format": "latex", "target": "declared.tex"}])

    convert_case(case_root)

    output_root = case_root / "outputs" / "build" / "formatted"
    assert (output_root / "declared.tex").exists()
    assert not (output_root / "undeclared.tex").exists()
