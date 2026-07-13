from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Subagent_integrate" / "scripts"))
sys.path.insert(0, str(ROOT / "Subagent_check" / "scripts"))

import check_lib  # noqa: E402
import integration_lib  # noqa: E402


def test_requested_capabilities_are_ready_in_shared_example() -> None:
    case_root = ROOT / "Subagent_integrate" / "examples" / "example_research" / "example_case"
    manifest = integration_lib.build_coordination_manifest(case_root)

    assert manifest["active_mode"] == "integration"
    assert manifest["blockers"] == []
    assert all(manifest["capability_status"][mode] == "ready" for mode in manifest["requested_capabilities"])


def test_unrequested_capabilities_do_not_block(tmp_path: Path) -> None:
    case_root = tmp_path / "missing_research" / "integration_case"
    (case_root / "manifests").mkdir(parents=True)
    integration_lib.write_json(
        integration_lib.manifest_path(case_root),
        {"requested_capabilities": ["presentation"]},
    )

    manifest = integration_lib.build_coordination_manifest(case_root)

    assert manifest["active_mode"] == "presentation"
    assert manifest["capability_status"]["evidence"] == "not_requested"
    assert manifest["blockers"] == ["Requested capability is not ready: presentation."]


def test_check_resolves_linked_case_without_mutating_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    check_lib.WORKSPACE_ROOT = workspace
    check_case = workspace / "Subagent_check" / "examples" / "example_research" / "example_case"
    integration_case = workspace / "Subagent_integrate" / "examples" / "example_research" / "example_case"
    target_case = workspace / "Subagent_evidence" / "examples" / "example_research" / "evidence_case"
    target_case.mkdir(parents=True)
    (integration_case / "manifests").mkdir(parents=True)
    (check_case / "manifests").mkdir(parents=True)

    coordination = {
        "research_case": "example_research",
        "linked_cases": [
            {
                "capability": "evidence",
                "subagent": "Subagent_evidence",
                "child_case": "evidence_case",
                "relative_path": os.path.relpath(target_case, check_case).replace("\\", "/"),
            }
        ],
    }
    (integration_case / "manifests" / "research_coordination_manifest.json").write_text(json.dumps(coordination), encoding="utf-8")
    manifest = check_lib.default_check_manifest(check_case)
    manifest["coordination_case_ref"] = os.path.relpath(integration_case, check_case).replace("\\", "/")
    check_lib.write_json(check_lib.manifest_path(check_case), manifest)

    report = check_lib.run_check(check_case)

    assert report["status"] == "pass"
    assert report["target_snapshot"][0]["present"] is True
    assert list(target_case.iterdir()) == []
