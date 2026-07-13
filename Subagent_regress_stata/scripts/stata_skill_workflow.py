from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from skill_workspace import DATA_DIR, OUTPUT_RESULTS_FIGURES_DIR, OUTPUT_RESULTS_LOGS_DIR, OUTPUT_RESULTS_TABLES_DIR, OUTPUT_SPECS_DIR, ensure_workspace_dirs, infer_column_candidates, list_supported_data_files, load_data_file, sanitize_for_json, save_json
    from stata.capability_registry import CAPABILITY_REGISTRY
except ModuleNotFoundError:
    from scripts.skill_workspace import DATA_DIR, OUTPUT_RESULTS_FIGURES_DIR, OUTPUT_RESULTS_LOGS_DIR, OUTPUT_RESULTS_TABLES_DIR, OUTPUT_SPECS_DIR, ensure_workspace_dirs, infer_column_candidates, list_supported_data_files, load_data_file, sanitize_for_json, save_json
    from scripts.stata.capability_registry import CAPABILITY_REGISTRY


SPEC_DIR = OUTPUT_SPECS_DIR
LOG_DIR = OUTPUT_RESULTS_LOGS_DIR
TABLE_DIR = OUTPUT_RESULTS_TABLES_DIR
FIGURE_DIR = OUTPUT_RESULTS_FIGURES_DIR
DEFAULT_SPEC_PATH = SPEC_DIR / "task_spec.json"
DEFAULT_DIAGNOSTICS_PATH = SPEC_DIR / "data_diagnostics.json"
DEFAULT_TEMPLATE_PATH = SPEC_DIR / "task_template.json"
DEFAULT_DO_PATH = SPEC_DIR / "task.do"
DEFAULT_PROJECT_TITLE = "stata 技能临时任务工作台"


def ensure_skill_output_dirs() -> None:
    ensure_workspace_dirs()


def _stdin_available() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()


def prompt_text(prompt: str, default: str) -> str:
    if not _stdin_available():
        return default
    try:
        answer = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        return default
    return answer or default


def prompt_yes_no(prompt: str, default: bool) -> bool:
    if not _stdin_available():
        return default
    default_text = "Y/n" if default else "y/N"
    try:
        answer = input(f"{prompt} ({default_text}): ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in {"y", "yes", "1", "是"}


def detect_year_span(df: pd.DataFrame, time_candidates: list[str]) -> dict[str, Any] | None:
    if not time_candidates:
        return None
    column = time_candidates[0]
    numeric = pd.to_numeric(df[column], errors="coerce").dropna()
    if numeric.empty:
        return None
    return {"column": column, "min": float(numeric.min()), "max": float(numeric.max())}


def detect_duplicate_keys(df: pd.DataFrame, id_candidates: list[str], time_candidates: list[str]) -> dict[str, Any]:
    if not id_candidates or not time_candidates:
        return {"checked": False, "duplicate_count": None, "key_columns": []}
    key_columns = [id_candidates[0], time_candidates[0]]
    duplicate_count = int(df.duplicated(key_columns).sum())
    return {"checked": True, "duplicate_count": duplicate_count, "key_columns": key_columns}


def choose_fixed_effect_candidates(candidates: dict[str, list[str]]) -> list[str]:
    fe_candidates: list[str] = []
    if candidates["id"]:
        fe_candidates.append(candidates["id"][0])
    if candidates["time"]:
        fe_candidates.append(candidates["time"][0])
    for column in candidates["cluster"]:
        if column not in fe_candidates:
            fe_candidates.append(column)
    return fe_candidates[:6]


def profile_dataset(path: Path) -> dict[str, Any]:
    df = load_data_file(path)
    candidates = infer_column_candidates(df)
    missing_share = df.isna().mean().sort_values(ascending=False).head(15).rename_axis("column").reset_index(name="missing_share")
    return sanitize_for_json(
        {
            "file_name": path.name,
            "path": str(path),
            "n_rows": int(len(df)),
            "n_cols": int(len(df.columns)),
            "columns": [str(column) for column in df.columns],
            "preview_rows": sanitize_for_json(df.head(3).to_dict(orient="records")),
            "candidate_columns": {
                "id": candidates["id"][:8],
                "time": candidates["time"][:8],
                "cluster": candidates["cluster"][:8],
                "fixed_effect": choose_fixed_effect_candidates(candidates),
                "numeric": candidates["numeric"][:20],
            },
            "missing_top": missing_share.to_dict(orient="records"),
            "year_span": detect_year_span(df, candidates["time"]),
            "duplicate_key_check": detect_duplicate_keys(df, candidates["id"], candidates["time"]),
        }
    )


def build_data_diagnostics(files: list[Path]) -> dict[str, Any]:
    if not files:
        return {
            "generated_from": [],
            "profiles": [],
            "comparison": {},
            "recommendation": {"strategy": "missing_data", "reason": "data 里还没有可分析的数据文件。"},
        }
    profiles = [profile_dataset(path) for path in files]
    recommendation = {
        "strategy": "single_file" if len(files) == 1 else "split_analysis_lines",
        "reason": "只有一个数据文件，先按单线分析。" if len(files) == 1 else "检测到多个数据文件，默认先分开跑，不直接硬合并。",
    }
    comparison: dict[str, Any] = {}
    if len(profiles) >= 2:
        first = profiles[0]
        second = profiles[1]
        comparison = {
            "common_columns": sorted(set(first["columns"]) & set(second["columns"])),
            "common_column_count": len(set(first["columns"]) & set(second["columns"])),
            "first_only_count": len(set(first["columns"]) - set(second["columns"])),
            "second_only_count": len(set(second["columns"]) - set(first["columns"])),
        }
    return {"generated_from": [path.name for path in files], "profiles": profiles, "comparison": comparison, "recommendation": recommendation}


def choose_numeric_defaults(profile: dict[str, Any]) -> tuple[str, str, list[str]]:
    numeric = list(profile["candidate_columns"].get("numeric", []))
    if len(numeric) < 2:
        raise ValueError(f"{profile['file_name']} 里数值列太少，当前没法自动生成回归设定。")
    depvar = numeric[0]
    core = numeric[1]
    controls = [column for column in numeric[2:5] if column not in {depvar, core}]
    return depvar, core, controls


def build_capability_snapshot() -> list[dict[str, Any]]:
    return sanitize_for_json(CAPABILITY_REGISTRY)


def build_task_request(diagnostics: dict[str, Any]) -> dict[str, Any]:
    summary = []
    for profile in diagnostics.get("profiles", []):
        summary.append(
            {
                "data_file": profile["file_name"],
                "id_candidates": profile["candidate_columns"].get("id", [])[:3],
                "time_candidates": profile["candidate_columns"].get("time", [])[:3],
                "numeric_candidates": profile["candidate_columns"].get("numeric", [])[:8],
            }
        )
    return {
        "mode": "temporary_task",
        "goal": "先做数据诊断，再按本次任务临时组装能力，不保留默认主线。",
        "selected_capabilities": [],
        "requested_outputs": ["task_spec", "task.do", "model_results", "quality_checks"],
        "notes": "当前默认不自动塞模型；只有明确指定后才会进入执行。",
        "data_candidates": summary,
    }


def build_empty_line(profile: dict[str, Any]) -> dict[str, Any]:
    depvar_default, core_default, controls_default = choose_numeric_defaults(profile)
    id_default = profile["candidate_columns"]["id"][0] if profile["candidate_columns"]["id"] else ""
    time_default = profile["candidate_columns"]["time"][0] if profile["candidate_columns"]["time"] else ""
    cluster_default = profile["candidate_columns"]["cluster"][:1]
    fixed_effects = [item for item in [id_default, time_default] if item]
    return {
        "line_id": Path(str(profile["file_name"])).stem,
        "line_type": "temporary_task",
        "title": f"{profile['file_name']} 临时任务",
        "data_file": profile["file_name"],
        "sample_filters": [],
        "winsorize": {"enabled": False, "lower": 0.01, "upper": 0.99},
        "recommended_roles": {
            "depvar": depvar_default,
            "core_var": core_default,
            "controls": controls_default,
            "id": id_default or None,
            "time": time_default or None,
            "cluster": cluster_default,
            "fixed_effects": fixed_effects,
        },
        "available_capabilities": [item["capability_id"] for item in CAPABILITY_REGISTRY],
        "selected_capabilities": [],
        "modules": [],
        "did": {"enabled": False},
        "parallel_trends": {"enabled": False},
        "matching": {"enabled": False},
        "placebo": {"enabled": False},
    }


def maybe_collect_interactive_modules(line: dict[str, Any]) -> dict[str, Any]:
    if not _stdin_available():
        return line
    role_defaults = dict(line["recommended_roles"])
    depvar = prompt_text(f"{line['data_file']} 的因变量", str(role_defaults.get("depvar") or ""))
    core_var = prompt_text(f"{line['data_file']} 的核心解释变量", str(role_defaults.get("core_var") or ""))
    controls_default = ",".join(role_defaults.get("controls") or [])
    controls = [item.strip() for item in prompt_text(f"{line['data_file']} 的控制变量，多个用逗号分开", controls_default).split(",") if item.strip()]
    id_column = str(role_defaults.get("id") or "")
    time_column = str(role_defaults.get("time") or "")
    cluster = list(role_defaults.get("cluster") or [])
    fixed_effects = list(role_defaults.get("fixed_effects") or [])
    modules: list[dict[str, Any]] = []
    selected_capabilities: list[str] = []
    if prompt_yes_no(f"{line['data_file']} 要不要加一条基准固定效应回归", True):
        selected_capabilities.append("baseline_fe")
        modules.append(
            {
                "module_type": "baseline",
                "name": "baseline_core",
                "capability_id": "baseline_fe",
                "models": [
                    {
                        "label": "m1",
                        "capability_id": "baseline_fe",
                        "estimator": "reghdfe",
                        "depvar": depvar,
                        "regressors": [core_var, *controls],
                        "absorb": fixed_effects,
                        "cluster": cluster,
                        "focus_terms": [core_var],
                        "roles": {"depvar": depvar, "core_var": core_var, "controls": controls, "id": id_column, "time": time_column, "cluster": cluster},
                    }
                ],
            }
        )
    line["selected_capabilities"] = selected_capabilities
    line["modules"] = modules
    return line


def flatten_models(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for line in lines:
        for module in line.get("modules", []):
            for model in module.get("models", []):
                flattened.append(
                    {
                        "line_id": line["line_id"],
                        "data_file": line["data_file"],
                        "module_type": module["module_type"],
                        "module_name": module["name"],
                        "capability_id": model.get("capability_id") or module.get("capability_id"),
                        "label": model["label"],
                        "estimator": model["estimator"],
                        "depvar": model["depvar"],
                        "regressors": list(model.get("regressors", [])),
                        "absorb": list(model.get("absorb", [])),
                        "cluster": list(model.get("cluster", [])),
                        "options": list(model.get("options", [])),
                        "focus_terms": list(model.get("focus_terms", [])),
                        "panel_settings": model.get("panel_settings"),
                        "iv_endogenous": model.get("iv_endogenous"),
                        "iv_instruments": list(model.get("iv_instruments", [])),
                        "ivar": model.get("ivar"),
                        "timevar": model.get("timevar"),
                        "gvar": model.get("gvar"),
                        "roles": model.get("roles", {}),
                    }
                )
    return flattened


def build_generic_template() -> dict[str, Any]:
    return {
        "project_title": DEFAULT_PROJECT_TITLE,
        "data_diagnostics": "output/specs/data_diagnostics.json",
        "task_request": {
            "mode": "temporary_task",
            "goal": "按这次需求临时组装模型能力",
            "selected_capabilities": [],
            "requested_outputs": ["task_spec", "task.do", "model_results", "quality_checks"],
        },
        "analysis_plan": {
            "capability_registry": "scripts/stata/capability_registry.py",
            "package_requirements": [],
            "analysis_lines": [],
        },
        "output_layout": {"specs": "output/specs", "results": "output/results", "runtime": "output/runtime"},
    }


def collect_package_requirements(lines: list[dict[str, Any]]) -> list[str]:
    packages: list[str] = []
    package_map = {item["capability_id"]: item.get("package_requirements", []) for item in CAPABILITY_REGISTRY}
    for line in lines:
        for capability_id in line.get("selected_capabilities", []):
            for package in package_map.get(capability_id, []):
                if package not in packages:
                    packages.append(package)
        for module in line.get("modules", []):
            capability_id = module.get("capability_id")
            for package in package_map.get(str(capability_id), []):
                if package not in packages:
                    packages.append(package)
            for model in module.get("models", []):
                capability_id = str(model.get("capability_id") or capability_id)
                for package in package_map.get(capability_id, []):
                    if package not in packages:
                        packages.append(package)
    return packages


def build_task_spec(diagnostics: dict[str, Any]) -> dict[str, Any]:
    lines = [maybe_collect_interactive_modules(build_empty_line(profile)) for profile in diagnostics.get("profiles", [])]
    project_title = prompt_text("这次项目名", DEFAULT_PROJECT_TITLE) if lines else DEFAULT_PROJECT_TITLE
    task_request = build_task_request(diagnostics)
    task_request["selected_capabilities"] = sorted({capability for line in lines for capability in line.get("selected_capabilities", [])})
    analysis_plan = {
        "capability_registry": "scripts/stata/capability_registry.py",
        "capabilities": build_capability_snapshot(),
        "package_requirements": collect_package_requirements(lines),
        "analysis_lines": lines,
    }
    return sanitize_for_json(
        {
            "project_title": project_title,
            "data_diagnostics": "output/specs/data_diagnostics.json",
            "task_request": task_request,
            "analysis_plan": analysis_plan,
            "models": flatten_models(lines),
            "output_layout": {"specs": "output/specs", "results": "output/results", "runtime": "output/runtime"},
        }
    )


def spec_has_explicit_models(spec: dict[str, Any]) -> bool:
    plan = dict(spec.get("analysis_plan") or {})
    lines = list(plan.get("analysis_lines") or [])
    if any(module.get("models") for line in lines for module in line.get("modules", [])):
        return True
    task_request = dict(spec.get("task_request") or {})
    return bool(task_request.get("locked"))


def load_existing_spec_if_locked() -> dict[str, Any] | None:
    if not DEFAULT_SPEC_PATH.exists():
        return None
    try:
        spec = __import__("json").loads(DEFAULT_SPEC_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    return spec if spec_has_explicit_models(spec) else None


def write_default_workflow_artifacts() -> dict[str, Path]:
    ensure_skill_output_dirs()
    files = list_supported_data_files()
    diagnostics = build_data_diagnostics(files)
    save_json(DEFAULT_DIAGNOSTICS_PATH, diagnostics)
    save_json(DEFAULT_TEMPLATE_PATH, build_generic_template())
    if not files:
        raise FileNotFoundError(f"{DATA_DIR} 里还没有 Excel、CSV 或 dta 数据文件。")
    existing_locked_spec = load_existing_spec_if_locked()
    spec = existing_locked_spec if existing_locked_spec is not None else build_task_spec(diagnostics)
    save_json(DEFAULT_SPEC_PATH, spec)
    return {"diagnostics": DEFAULT_DIAGNOSTICS_PATH, "spec": DEFAULT_SPEC_PATH, "template": DEFAULT_TEMPLATE_PATH, "do_file": DEFAULT_DO_PATH}
