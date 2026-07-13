from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from skill_workspace import DATA_DIR, OUTPUT_SPECS_DIR, save_json
    from stata.capability_registry import capability_map
except ModuleNotFoundError:
    from scripts.skill_workspace import DATA_DIR, OUTPUT_SPECS_DIR, save_json
    from scripts.stata.capability_registry import capability_map


MANIFEST_PATH = OUTPUT_SPECS_DIR / "task_manifest.json"
SPEC_PATH = OUTPUT_SPECS_DIR / "task_spec.json"


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def line_id_from_file(data_file: str) -> str:
    return Path(data_file).stem


def module_name_from_capability(capability_id: str, label: str) -> str:
    return f"{capability_id}_{label}".strip("_")


def normalize_csdid_options(options: list[str], target_agg: str) -> list[str]:
    normalized = [str(option) for option in options if str(option).strip()]
    filtered = [option for option in normalized if not option.startswith("agg(")]
    filtered.append(target_agg)
    return filtered


def default_csdid_event_focus_terms() -> list[str]:
    return ["Pre_avg", "Post_avg", "Tm5", "Tm4", "Tm3", "Tm2", "Tm1", "Tp0", "Tp1", "Tp2", "Tp3", "Tp4", "Tp5"]


def build_model(item: dict[str, Any], capability: dict[str, Any]) -> dict[str, Any]:
    roles = dict(item.get("roles") or {})
    depvar = str(item["depvar"])
    regressors = [str(x) for x in item.get("regressors") or []]
    if not regressors:
        core_var = roles.get("core_var")
        controls = ensure_list(roles.get("controls"))
        treatment = roles.get("treatment")
        if core_var:
            regressors = [str(core_var), *[str(x) for x in controls]]
        elif treatment:
            regressors = [str(treatment), *[str(x) for x in controls]]
        else:
            regressors = [str(x) for x in controls]
    focus_terms = [str(x) for x in item.get("focus_terms") or []]
    if not focus_terms:
        default_focus = capability.get("default_focus_term_rule")
        if default_focus in roles:
            focus_terms = [str(roles[default_focus])]
        elif default_focus == "ATT":
            focus_terms = ["ATT"]
        elif default_focus == "csdid_event_terms":
            focus_terms = default_csdid_event_focus_terms()
        elif default_focus == "core_var" and roles.get("core_var"):
            focus_terms = [str(roles["core_var"])]
        elif default_focus == "treatment" and roles.get("treatment"):
            focus_terms = [str(roles["treatment"])]
        elif default_focus == "endogenous" and roles.get("endogenous"):
            focus_terms = [str(roles["endogenous"])]
    model = {
        "label": str(item["label"]),
        "capability_id": str(item["capability_id"]),
        "estimator": str(item.get("estimator") or capability["estimator"]),
        "depvar": depvar,
        "regressors": regressors,
        "focus_terms": focus_terms,
        "roles": roles,
    }
    if "options" in item:
        model["options"] = [str(x) for x in item.get("options") or []]
    if item.get("post_estimation") is not None:
        model["post_estimation"] = dict(item["post_estimation"])
    for key in ("absorb", "cluster", "iv_instruments"):
        if item.get(key) is not None:
            model[key] = [str(x) for x in ensure_list(item.get(key))]
    for key in ("iv_endogenous", "ivar", "timevar", "gvar"):
        if item.get(key) is not None:
            model[key] = str(item.get(key))
    panel_settings = dict(item.get("panel_settings") or {})
    if panel_settings:
        model["panel_settings"] = panel_settings
    return model


def align_csdid_event_models(models: list[dict[str, Any]]) -> None:
    simple_model: dict[str, Any] | None = None
    for model in models:
        if str(model.get("capability_id")) == "did_csdid":
            simple_model = model
            break
    if simple_model is None:
        return
    simple_options = [str(option) for option in simple_model.get("options", [])]
    aligned_event_options = normalize_csdid_options(simple_options, "agg(event)")
    for model in models:
        if str(model.get("capability_id")) != "did_csdid_event":
            continue
        if "options" not in model:
            model["options"] = aligned_event_options
        if not model.get("focus_terms"):
            model["focus_terms"] = default_csdid_event_focus_terms()


def build_spec(manifest: dict[str, Any]) -> dict[str, Any]:
    capabilities = capability_map()
    models_by_file: dict[str, list[dict[str, Any]]] = {}
    selected_capabilities: dict[str, list[str]] = {}
    for item in manifest.get("models", []):
        capability_id = str(item["capability_id"])
        capability = capabilities[capability_id]
        data_file = str(item["data_file"])
        models_by_file.setdefault(data_file, []).append(build_model(item, capability))
        selected_capabilities.setdefault(data_file, [])
        if capability_id not in selected_capabilities[data_file]:
            selected_capabilities[data_file].append(capability_id)
    analysis_lines: list[dict[str, Any]] = []
    package_requirements: list[str] = []
    for data_file, models in models_by_file.items():
        align_csdid_event_models(models)
        modules: list[dict[str, Any]] = []
        for model in models:
            capability_id = str(model["capability_id"])
            module_type = capability_id
            name = module_name_from_capability(capability_id, str(model["label"]))
            modules.append(
                {
                    "module_type": module_type,
                    "name": name,
                    "capability_id": capability_id,
                    "models": [model],
                }
            )
            for package in capabilities[capability_id].get("package_requirements", []):
                if package not in package_requirements:
                    package_requirements.append(package)
        analysis_lines.append(
            {
                "line_id": line_id_from_file(data_file),
                "line_type": "explicit_models",
                "title": f"{data_file} 指定模型任务",
                "data_file": data_file,
                "sample_filters": ensure_list(manifest.get("sample_filters")),
                "winsorize": dict(manifest.get("winsorize") or {"enabled": False, "lower": 0.01, "upper": 0.99}),
                "selected_capabilities": selected_capabilities[data_file],
                "modules": modules,
                "did": dict(manifest.get("did") or {"enabled": False}),
                "parallel_trends": dict(manifest.get("parallel_trends") or {"enabled": False}),
                "matching": dict(manifest.get("matching") or {"enabled": False}),
                "placebo": dict(manifest.get("placebo") or {"enabled": False}),
            }
        )
    return {
        "project_title": str(manifest.get("project_title") or "stata 技能显式模型任务"),
        "data_diagnostics": "output/specs/data_diagnostics.json",
        "task_request": {
            "mode": "explicit_models",
            "goal": str(manifest.get("goal") or "按给定模型清单直接执行"),
            "selected_capabilities": sorted({cap for caps in selected_capabilities.values() for cap in caps}),
            "requested_outputs": ["task_spec", "task.do", "model_results", "quality_checks"],
            "locked": True,
        },
        "analysis_plan": {
            "capability_registry": "scripts/stata/capability_registry.py",
            "package_requirements": package_requirements,
            "analysis_lines": analysis_lines,
        },
        "models": [model for models in models_by_file.values() for model in models],
        "output_layout": {"specs": "output/specs", "results": "output/results", "runtime": "output/runtime"},
    }


def example_manifest() -> dict[str, Any]:
    return {
        "project_title": "示例：指定模型任务",
        "goal": "按模型清单直接执行",
        "models": [
            {
                "label": "m1",
                "capability_id": "ppml_fe",
                "data_file": "your_data.dta",
                "depvar": "y",
                "roles": {"core_var": "x_core", "controls": ["c1", "c2"]},
                "regressors": ["x_core", "c1", "c2"],
                "absorb": ["id", "year"],
                "cluster": ["id"],
            }
        ],
    }


def main() -> None:
    OUTPUT_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_PATH.exists():
        save_json(MANIFEST_PATH, example_manifest())
        print(f"完成 已生成示例清单：{MANIFEST_PATH}")
        print("提示 你把要跑的模型填进 task_manifest.json，再重新运行这个脚本。")
        return
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known_files = {path.name for path in DATA_DIR.iterdir() if path.is_file()} if DATA_DIR.exists() else set()
    for item in manifest.get("models", []):
        data_file = str(item["data_file"])
        if data_file not in known_files:
            raise FileNotFoundError(f"data 里找不到这个文件：{data_file}")
    spec = build_spec(manifest)
    save_json(SPEC_PATH, spec)
    print(f"完成 已按模型清单写入：{SPEC_PATH}")
    print("提示 现在可以直接运行 python scripts/run_stata_skill_workflow.py")


if __name__ == "__main__":
    main()
