from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from skill_workspace import DATA_DIR, OUTPUT_RESULTS_SUMMARIES_DIR, OUTPUT_SPECS_DIR, infer_column_candidates, load_data_file, sanitize_for_json, save_json
except ModuleNotFoundError:
    from scripts.skill_workspace import DATA_DIR, OUTPUT_RESULTS_SUMMARIES_DIR, OUTPUT_SPECS_DIR, infer_column_candidates, load_data_file, sanitize_for_json, save_json


MANIFEST_PATH = DATA_DIR / "data_sources.json"
SUMMARY_PATH = OUTPUT_RESULTS_SUMMARIES_DIR / "asset_scan_summary.json"
SPEC_SUMMARY_PATH = OUTPUT_SPECS_DIR / "asset_scan_summary.json"


def preview_frame(path: Path) -> dict[str, Any]:
    df = load_data_file(path)
    candidates = infer_column_candidates(df)
    return {
        "path": str(path),
        "file_name": path.name,
        "n_rows": int(len(df)),
        "n_cols": int(len(df.columns)),
        "columns": [str(column) for column in df.columns[:50]],
        "candidate_columns": candidates,
        "preview_rows": sanitize_for_json(df.head(3).to_dict(orient="records")),
    }


def direct_assets() -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    if not DATA_DIR.exists():
        return assets
    for path in sorted(DATA_DIR.iterdir(), key=lambda item: item.name.lower()):
        if path.name == "data_sources.json":
            continue
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls", ".dta"}:
            item = preview_frame(path)
            item["asset_type"] = "direct_file"
            assets.append(item)
        elif path.is_dir():
            assets.append({"asset_type": "direct_folder", "path": str(path), "file_name": path.name})
    return assets


def manifest_assets() -> list[dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        return []
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    items = payload.get("sources") or []
    summary: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["asset_type"] = "manifest_entry"
        summary.append(sanitize_for_json(row))
    return summary


def build_summary() -> dict[str, Any]:
    return {
        "stable_input_root": str(DATA_DIR),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_assets": manifest_assets(),
        "direct_assets": direct_assets(),
    }


def main() -> None:
    summary = build_summary()
    save_json(SUMMARY_PATH, summary)
    save_json(SPEC_SUMMARY_PATH, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
