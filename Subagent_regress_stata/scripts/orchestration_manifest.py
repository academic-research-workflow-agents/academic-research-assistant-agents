from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from skill_workspace import OUTPUT_RESULTS_FOLLOWUPS_DIR, OUTPUT_SPECS_DIR, save_json
except ModuleNotFoundError:
    from scripts.skill_workspace import OUTPUT_RESULTS_FOLLOWUPS_DIR, OUTPUT_SPECS_DIR, save_json


ASSET_SCAN_PATH = OUTPUT_SPECS_DIR / "asset_scan_summary.json"


def read_asset_scan() -> dict[str, Any]:
    if not ASSET_SCAN_PATH.exists():
        return {"manifest_assets": [], "direct_assets": []}
    return json.loads(ASSET_SCAN_PATH.read_text(encoding="utf-8"))


def stage_manifest_path(stage: str) -> Path:
    return OUTPUT_SPECS_DIR / f"{stage}_manifest.json"


def stage_execution_mode(stage: str) -> str:
    if stage == "final_design":
        return "single_design_do"
    return "master_do"


def stage_note(stage: str) -> str:
    notes = {
        "baseline": "baseline 阶段优先使用一个主 do-file，在内部循环设计集合。",
        "followup": "follow-up 阶段优先使用一个小批次主 do-file，在内部循环入围设计。",
        "final_design": "只有最后收敛到最终设计时，才导出单设计 do-file。",
    }
    return notes[stage]


def build_manifest(stage: str) -> dict[str, Any]:
    if stage not in {"baseline", "followup", "final_design"}:
        raise ValueError(f"Unsupported stage: {stage}")
    payload: dict[str, Any] = {
        "stage": stage,
        "execution_mode": stage_execution_mode(stage),
        "note": stage_note(stage),
    }
    if stage == "baseline":
        assets = read_asset_scan()
        payload["asset_candidates"] = [*(assets.get("manifest_assets") or []), *(assets.get("direct_assets") or [])]
        payload["selected_assets"] = []
        payload["shared_model_design"] = {
            "model_columns": [],
            "fixed_effects": [],
            "cluster_level": [],
        }
    elif stage == "followup":
        payload["selection_source"] = str(OUTPUT_RESULTS_FOLLOWUPS_DIR / "followup_candidates.json")
        payload["selected_designs"] = []
        payload["followup_modules"] = []
    else:
        payload["selected_design"] = {}
        payload["requested_exports"] = ["tables", "figures", "logs"]
    return payload


def write_manifest(stage: str) -> Path:
    path = stage_manifest_path(stage)
    save_json(path, build_manifest(stage))
    return path
