from __future__ import annotations

import json
import math
import os
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = SUBAGENT_ROOT / "examples"


def resolve_active_case_root() -> Path:
    env_case_root = os.environ.get("REGRESSION_CASE_ROOT")
    if env_case_root:
        candidate = Path(env_case_root).resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"REGRESSION_CASE_ROOT does not exist: {candidate}")

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if candidate.parent.parent == EXAMPLES_ROOT:
            return candidate
        if candidate.parent == EXAMPLES_ROOT and (candidate / "AGENTS.md").exists():
            return candidate

    raise RuntimeError(
        "Subagent_regress_stata scripts now require an active child_case. "
        "Set REGRESSION_CASE_ROOT or run the command from examples/<research_case>/<child_case>."
    )


ROOT = resolve_active_case_root()
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
ASSETS_TEMPLATES_DIR = ASSETS_DIR / "templates"
ASSETS_REFERENCES_DIR = ASSETS_DIR / "references"
ASSETS_EXTERNAL_SCRIPTS_DIR = ASSETS_DIR / "external_scripts"

OUTPUT_DIR = Path(os.environ.get("REGRESSION_OUTPUT_DIR", str(ROOT / "outputs"))).resolve()
OUTPUT_SPECS_DIR = OUTPUT_DIR / "specs"
OUTPUT_RESULTS_DIR = OUTPUT_DIR / "results"
OUTPUT_RUNTIME_DIR = OUTPUT_DIR / "runtime"
OUTPUT_RESULTS_LOGS_DIR = OUTPUT_RESULTS_DIR / "logs"
OUTPUT_RESULTS_TABLES_DIR = OUTPUT_RESULTS_DIR / "tables"
OUTPUT_RESULTS_FIGURES_DIR = OUTPUT_RESULTS_DIR / "figures"
OUTPUT_RESULTS_SUMMARIES_DIR = OUTPUT_RESULTS_DIR / "summaries"
OUTPUT_RESULTS_FOLLOWUPS_DIR = OUTPUT_RESULTS_DIR / "followups"
OUTPUT_RUNTIME_LOGS_DIR = OUTPUT_RUNTIME_DIR / "logs"
OUTPUT_RUNTIME_TMP_DIR = OUTPUT_RUNTIME_DIR / "tmp"

SUPPORTED_DATA_SUFFIXES = (".xlsx", ".xls", ".csv", ".dta")
ROOT_LOG_SUFFIXES = {".log"}
ROOT_LOG_KEEP = {"AGENTS.md", "README.md"}
SCRIPT_ARTIFACT_DIR_NAMES = {"__pycache__"}
SCRIPT_ARTIFACT_FILE_PATTERNS = (
    "*.log",
    "*.tmp",
    "*_debug.py",
    "*_debug.do",
    "*_probe.py",
    "*_probe.do",
    "tmp_*.py",
    "tmp_*.do",
)


def ensure_workspace_dirs() -> None:
    for path in (
        ASSETS_DIR,
        ASSETS_TEMPLATES_DIR,
        ASSETS_REFERENCES_DIR,
        ASSETS_EXTERNAL_SCRIPTS_DIR,
        OUTPUT_SPECS_DIR,
        OUTPUT_RESULTS_LOGS_DIR,
        OUTPUT_RESULTS_TABLES_DIR / "zh",
        OUTPUT_RESULTS_TABLES_DIR / "en",
        OUTPUT_RESULTS_FIGURES_DIR / "zh",
        OUTPUT_RESULTS_FIGURES_DIR / "en",
        OUTPUT_RESULTS_SUMMARIES_DIR,
        OUTPUT_RESULTS_FOLLOWUPS_DIR,
        OUTPUT_RUNTIME_LOGS_DIR,
        OUTPUT_RUNTIME_TMP_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def sanitize_for_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_for_json(item) for item in value]
    return str(value)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_for_json(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_name(name: str) -> str:
    return re.sub(r"[\W_]+", "", str(name).lower())


def find_candidate_columns(columns: list[str], keywords: list[str]) -> list[str]:
    normalized_keywords = [normalize_name(item) for item in keywords]
    hits: list[str] = []
    for column in columns:
        normalized_column = normalize_name(column)
        if any(keyword in normalized_column for keyword in normalized_keywords):
            hits.append(column)
    return hits


def infer_column_candidates(df: pd.DataFrame) -> dict[str, list[str]]:
    columns = [str(column) for column in df.columns]
    numeric_columns = [column for column in columns if pd.api.types.is_numeric_dtype(df[column])]
    return {
        "id": find_candidate_columns(columns, ["id", "代码", "企业", "公司", "股票", "firm", "stk", "个体"]),
        "time": find_candidate_columns(columns, ["year", "年份", "时间", "date", "period"]),
        "cluster": find_candidate_columns(columns, ["行业", "industry", "城市", "city", "省", "province", "地区", "cluster"]),
        "numeric": numeric_columns,
    }


def list_supported_data_files() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    files = [path for path in DATA_DIR.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_DATA_SUFFIXES]
    return sorted(files, key=lambda item: item.name.lower())


def load_data_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path, encoding="utf-8-sig")
    if suffix == ".dta":
        return pd.read_stata(path, convert_categoricals=False)
    raise ValueError(f"不支持的数据格式：{path.suffix}")


def cleanup_output_dirs(remove_specs: bool = True, remove_results: bool = False) -> None:
    targets = [OUTPUT_RUNTIME_DIR]
    if remove_specs:
        targets.append(OUTPUT_SPECS_DIR)
    if remove_results:
        targets.append(OUTPUT_RESULTS_DIR)
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
    ensure_workspace_dirs()


def cleanup_root_logs() -> list[Path]:
    removed: list[Path] = []
    if not ROOT.exists():
        return removed
    for path in ROOT.iterdir():
        if not path.is_file():
            continue
        if path.name in ROOT_LOG_KEEP:
            continue
        if path.suffix.lower() not in ROOT_LOG_SUFFIXES:
            continue
        path.unlink(missing_ok=True)
        removed.append(path)
    return removed


def cleanup_script_artifacts() -> dict[str, list[Path]]:
    removed_dirs: list[Path] = []
    removed_files: list[Path] = []
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return {"dirs": removed_dirs, "files": removed_files}
    for path in scripts_dir.rglob("*"):
        if path.is_dir() and path.name in SCRIPT_ARTIFACT_DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
            removed_dirs.append(path)
    for pattern in SCRIPT_ARTIFACT_FILE_PATTERNS:
        for path in scripts_dir.rglob(pattern):
            if not path.is_file():
                continue
            path.unlink(missing_ok=True)
            removed_files.append(path)
    return {"dirs": removed_dirs, "files": removed_files}


def reset_for_new_project() -> None:
    cleanup_output_dirs(remove_specs=True, remove_results=True)
    cleanup_root_logs()
    cleanup_script_artifacts()
