from __future__ import annotations

import json
from pathlib import Path

try:
    from skill_workspace import DATA_DIR, save_json
except ModuleNotFoundError:
    from scripts.skill_workspace import DATA_DIR, save_json


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ARCHIVE_FALLBACK_NAME = "archive_" + "Subagent_" + "_".join(["customized", "regression"])
LEGACY_MANIFEST_CANDIDATES = [
    ROOT.parent / "archive_Subagent_regression" / "data" / "data_sources.json",
    ROOT.parent / LEGACY_ARCHIVE_FALLBACK_NAME / "data" / "data_sources.json",
]
TARGET_MANIFEST = DATA_DIR / "data_sources.json"


def main() -> None:
    if TARGET_MANIFEST.exists():
        print(f"跳过 目标 manifest 已存在：{TARGET_MANIFEST}")
        return
    legacy_manifest = next((path for path in LEGACY_MANIFEST_CANDIDATES if path.exists()), None)
    if legacy_manifest is None:
        print(f"跳过 没有找到历史 manifest：{LEGACY_MANIFEST_CANDIDATES[0]}")
        return
    payload = json.loads(legacy_manifest.read_text(encoding="utf-8"))
    save_json(TARGET_MANIFEST, payload)
    print(f"完成 已迁移历史 manifest：{TARGET_MANIFEST}")


if __name__ == "__main__":
    main()
