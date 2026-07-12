from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from providers import load_provider


ROOT = Path(__file__).resolve().parents[1]


class BuildError(Exception):
    pass


@dataclass(frozen=True)
class Combo:
    panel_group: str
    panel_grain: str
    key_template: str
    y_var: dict[str, Any]
    x_var: dict[str, Any]
    c_bundle: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build regression-ready panels from provider-driven specs.")
    parser.add_argument("--spec-file", type=Path, required=True)
    return parser.parse_args()


def resolve_case_root_from_spec(spec_file: Path) -> Path:
    resolved = spec_file.resolve()
    if resolved.parent.name in {"requests", "config"}:
        return resolved.parent.parent
    return resolved.parent


def build_output_paths(case_root: Path) -> dict[str, Path]:
    output_root = case_root / "outputs"
    paths = {
        "output_root": output_root,
        "panel_dir": output_root / "regression_panels",
        "rule_report_dir": output_root / "regression_panel_reports",
        "exception_dir": output_root / "regression_panel_exceptions",
        "manifest_dir": output_root / "regression_panel_manifest",
        "sync_manifest": output_root / "specs" / "data_sources.json",
    }
    assert_output_paths_in_case(case_root, paths)
    return paths


def assert_output_paths_in_case(case_root: Path, paths: dict[str, Path]) -> None:
    case_root_resolved = case_root.resolve()
    for label, path in paths.items():
        resolved = path.resolve()
        try:
            resolved.relative_to(case_root_resolved)
        except ValueError as error:
            raise BuildError(f"Output path for {label} escapes active child_case: {resolved}") from error


def ensure_dirs(paths: dict[str, Path]) -> None:
    for path in (
        paths["panel_dir"],
        paths["rule_report_dir"],
        paths["exception_dir"],
        paths["manifest_dir"],
        paths["sync_manifest"].parent,
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_xlsx(frame: pd.DataFrame, path: Path, sheet_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet_name)


def write_panel(frame: pd.DataFrame, path: Path, output_format: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "xlsx":
        write_xlsx(frame, path, "panel")
        return
    if output_format == "csv":
        frame.to_csv(path, index=False, encoding="utf-8-sig")
        return
    raise BuildError(f"Unsupported output_format: {output_format}")


def write_table(frame: pd.DataFrame, path: Path, output_format: str, sheet_name: str) -> None:
    if output_format == "xlsx":
        write_xlsx(frame, path, sheet_name)
        return
    if output_format == "csv":
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, encoding="utf-8-sig")
        return
    raise BuildError(f"Unsupported output_format: {output_format}")


def normalize_output_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    policy = dict(policy or {})
    return {
        "mode": policy.get("mode", "one_panel_per_regression_combo"),
        "output_format": str(policy.get("output_format", "xlsx")).lower(),
        "rule_report_format": str(policy.get("rule_report_format", "xlsx")).lower(),
        "exceptions_format": str(policy.get("exceptions_format", "xlsx")).lower(),
        "naming_pattern": policy.get("naming_pattern", "{panel_group}__{y_alias}__{x_alias}__{c_bundle_id}"),
        "sync_to_regression": bool(policy.get("sync_to_regression", policy.get("sync_to_regression", False))),
        "include_manifest": bool(policy.get("include_manifest", True)),
        "allow_failed_combos": bool(policy.get("allow_failed_combos", True))
    }


def load_and_expand_spec(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if "provider_ids" not in payload:
        raise BuildError("Build spec must include provider_ids.")
    case_root = resolve_case_root_from_spec(path)
    providers = {
        provider_id: load_provider(str(provider_id), case_root=case_root)
        for provider_id in payload.get("provider_ids", [])
    }
    candidate_variables = payload.get("candidate_variables", {})
    control_bundles = list(payload.get("control_bundles", []))
    source_assets = list(payload.get("source_assets", []))

    for provider in providers.values():
        source_assets.extend(provider.source_assets)
        control_bundles.extend(provider.control_bundles)
        for variable in provider.candidate_variables:
            role = variable["role"]
            if role == "dependent_variable":
                candidate_variables.setdefault("dependent_variables", []).append(variable)
            elif role == "independent_variable":
                candidate_variables.setdefault("independent_variables", []).append(variable)
            elif role == "control_variable":
                candidate_variables.setdefault("control_variables", []).append(variable)

    return {
        "providers": providers,
        "source_assets": source_assets,
        "candidate_variables": {
            "dependent_variables": list(candidate_variables.get("dependent_variables", [])),
            "independent_variables": list(candidate_variables.get("independent_variables", [])),
            "control_variables": list(candidate_variables.get("control_variables", []))
        },
        "control_bundles": control_bundles,
        "build_tasks": list(payload.get("build_tasks", [{"mode": "cartesian_by_group"}])),
        "output_policy": normalize_output_policy(payload.get("output_policy")),
        "sync_targets": list(payload.get("sync_targets", [])),
        "selection_filters": dict(payload.get("selection_filters", {})),
        "case_root": case_root,
    }


def group_compatible(y_var: dict[str, Any], x_var: dict[str, Any], c_bundle: dict[str, Any]) -> bool:
    return (
        len({y_var["panel_group"], x_var["panel_group"], c_bundle["panel_group"]}) == 1
        and len({y_var["panel_grain"], x_var["panel_grain"], c_bundle["panel_grain"]}) == 1
        and len({y_var["key_template"], x_var["key_template"], c_bundle["key_template"]}) == 1
    )


def expand_combos(spec: dict[str, Any]) -> list[Combo]:
    combos: list[Combo] = []
    selection_filters = spec.get("selection_filters", {})
    allowed_y_ids = set(selection_filters.get("y_ids", []))
    allowed_x_ids = set(selection_filters.get("x_ids", []))
    allowed_bundle_ids = set(selection_filters.get("c_bundle_ids", []))

    y_vars = [
        item for item in spec["candidate_variables"]["dependent_variables"]
        if not allowed_y_ids or item["id"] in allowed_y_ids
    ]
    x_vars = [
        item for item in spec["candidate_variables"]["independent_variables"]
        if not allowed_x_ids or item["id"] in allowed_x_ids
    ]
    control_bundles = [
        item for item in spec["control_bundles"]
        if not allowed_bundle_ids or item["id"] in allowed_bundle_ids
    ]
    bundle_lookup = {item["id"]: item for item in control_bundles}

    explicit_tasks = [item for item in spec["build_tasks"] if item["mode"] == "explicit_combos"]
    if explicit_tasks:
        for task in explicit_tasks:
            for combo_item in task.get("combos", []):
                y_var = next(item for item in y_vars if item["id"] == combo_item["y_id"])
                x_var = next(item for item in x_vars if item["id"] == combo_item["x_id"])
                c_bundle = bundle_lookup[combo_item["c_bundle_id"]]
                if not group_compatible(y_var, x_var, c_bundle):
                    raise BuildError("Explicit combo crosses panel_group, panel_grain, or key_template.")
                combos.append(Combo(y_var["panel_group"], y_var["panel_grain"], y_var["key_template"], y_var, x_var, c_bundle))
        return combos

    for y_var in y_vars:
        for x_var in x_vars:
            for c_bundle in control_bundles:
                if group_compatible(y_var, x_var, c_bundle):
                    combos.append(Combo(y_var["panel_group"], y_var["panel_grain"], y_var["key_template"], y_var, x_var, c_bundle))
    if not combos:
        raise BuildError("No valid Y/X/C combos under the same panel_group + panel_grain + key_template.")
    return combos


def apply_derivation(frame: pd.DataFrame, variable: dict[str, Any]) -> pd.Series:
    if not variable.get("is_derived"):
        return frame[variable["field_token"]]
    spec = variable.get("derivation_spec") or {}
    source_field = spec.get("source_field") or variable["field_token"]
    source = pd.to_numeric(frame[source_field], errors="coerce")
    operation = spec.get("operation")
    if operation == "log1p":
        return np.log1p(source.clip(lower=0))
    if operation == "log":
        return pd.Series(np.where(source > 0, np.log(source), np.nan), index=frame.index)
    if operation == "ratio":
        denominator = pd.to_numeric(frame[spec["denominator_field"]], errors="coerce")
        return pd.Series(np.where(denominator != 0, source / denominator, np.nan), index=frame.index)
    raise BuildError(f"Unsupported derivation operation: {operation}")


def _first_matching_column(columns: list[str], suffix: str) -> str | None:
    matches = [column for column in columns if column.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]
    return None


def derive_did_context_frame(frame: pd.DataFrame, asset: dict[str, Any]) -> pd.DataFrame:
    output = frame[["entity_key", "time_key"]].copy()
    numeric_time = pd.to_numeric(frame["time_key"], errors="coerce")
    ever_treated = pd.to_numeric(frame.get("Treat"), errors="coerce")
    post = pd.to_numeric(frame.get("Post"), errors="coerce")
    did_interaction = pd.to_numeric(frame.get("Treat_Post"), errors="coerce")

    policy_year_column = _first_matching_column(list(frame.columns), "_year")
    policy_month_column = _first_matching_column(list(frame.columns), "_month")
    policy_year = pd.to_numeric(frame[policy_year_column], errors="coerce") if policy_year_column else pd.Series(pd.NA, index=frame.index, dtype="Float64")
    treat_month = pd.to_numeric(frame[policy_month_column], errors="coerce") if policy_month_column else pd.Series(pd.NA, index=frame.index, dtype="Float64")

    treated_time = numeric_time.where(post.eq(1) & ever_treated.eq(1))
    first_treat_year = treated_time.groupby(frame["entity_key"]).transform("min")
    never_treated_flag = ever_treated.eq(0).astype("Int64")
    not_yet_treated_flag = (ever_treated.eq(1) & post.eq(0)).astype("Int64")
    event_time = numeric_time - first_treat_year

    output["treatment_indicator"] = did_interaction.astype("Int64")
    output["ever_treated"] = ever_treated.astype("Int64")
    output["post"] = post.astype("Int64")
    output["did_interaction"] = did_interaction.astype("Int64")
    output["first_treat_year"] = first_treat_year.astype("Int64")
    output["policy_year"] = policy_year.astype("Int64")
    output["event_time"] = event_time.astype("Int64")
    output["never_treated_flag"] = never_treated_flag
    output["not_yet_treated_flag"] = not_yet_treated_flag

    if "province_code" in frame.columns:
        output["province_cluster"] = frame["province_code"]
    if "city_code" in frame.columns:
        output["city_code"] = frame["city_code"]
    if policy_month_column:
        output["treat_month"] = treat_month.astype("Int64")

    notes = str(asset.get("notes", ""))
    source_id = str(asset.get("source_id", ""))
    if notes:
        output["treatment_branch"] = notes
    if source_id:
        output["treatment_level"] = source_id.split("_")[-1]
    return output


def prepare_variable_frame(providers: dict[str, Any], variable: dict[str, Any]) -> pd.DataFrame:
    provider = providers[variable["provider_id"]]
    asset = provider.get_source_asset(variable["source_id"])
    frame = provider.load_source_frame(variable["source_id"])
    if variable.get("field_token") not in frame.columns and not variable.get("is_derived"):
        raise BuildError(f"Missing field {variable['field_token']} in source {variable['source_id']}.")
    output = frame[["entity_key", "time_key"]].copy()
    for display_column in ("province_name", "city_name", "province_code"):
        if display_column in frame.columns:
            output[display_column] = frame[display_column]
    output[variable["alias"]] = apply_derivation(frame, variable)
    if asset.get("source_type") == "did_branch_panel":
        context_frame = derive_did_context_frame(frame, asset)
        output = output.merge(context_frame, on=["entity_key", "time_key"], how="left")
    return output


def build_panel_for_combo(combo: Combo, spec: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    control_lookup = {item["id"]: item for item in spec["candidate_variables"]["control_variables"]}
    selected_controls = [control_lookup[item] for item in combo.c_bundle["variable_ids"]]
    selected_variables = [combo.y_var, combo.x_var, *selected_controls]

    panel: pd.DataFrame | None = None
    selected_aliases: list[str] = []
    for variable in selected_variables:
        variable_frame = prepare_variable_frame(spec["providers"], variable)
        selected_aliases.append(variable["alias"])
        if panel is None:
            panel = variable_frame
        else:
            panel = panel.merge(variable_frame, on=["entity_key", "time_key"], how="outer", suffixes=("", "_dup"))
            duplicate_columns = [column for column in panel.columns if column.endswith("_dup")]
            if duplicate_columns:
                panel = panel.drop(columns=duplicate_columns)

    if panel is None:
        raise BuildError("Empty combo.")

    missing_summary = pd.DataFrame(
        [
            {
                "column": alias,
                "non_missing_count": int(panel[alias].notna().sum()),
                "missing_rate": float(panel[alias].isna().mean())
            }
            for alias in selected_aliases
        ]
    )
    fully_missing = missing_summary.loc[missing_summary["missing_rate"] >= 1.0, "column"].tolist()
    if fully_missing:
        raise BuildError(f"Critical variables fully missing: {fully_missing}")
    panel = panel.sort_values(["entity_key", "time_key"]).reset_index(drop=True)
    return panel, missing_summary


def make_panel_id(combo: Combo, pattern: str) -> str:
    return pattern.format(
        panel_group=combo.panel_group,
        y_alias=combo.y_var["alias"],
        x_alias=combo.x_var["alias"],
        c_bundle_id=combo.c_bundle["id"]
    )


def build_exception_frame(message: str) -> pd.DataFrame:
    return pd.DataFrame([{"message": message}])


def write_rule_report(path: Path, combo: Combo, missing_summary: pd.DataFrame, output_format: str) -> None:
    summary = pd.DataFrame(
        [
            {"item": "panel_group", "value": combo.panel_group},
            {"item": "panel_grain", "value": combo.panel_grain},
            {"item": "key_template", "value": combo.key_template},
            {"item": "y_id", "value": combo.y_var["id"]},
            {"item": "x_id", "value": combo.x_var["id"]},
            {"item": "c_bundle_id", "value": combo.c_bundle["id"]}
        ]
    )
    if output_format == "xlsx":
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            summary.to_excel(writer, index=False, sheet_name="summary")
            missing_summary.to_excel(writer, index=False, sheet_name="missing_summary")
        return
    if output_format == "csv":
        report = summary.copy()
        report["section"] = "summary"
        missing = missing_summary.copy()
        missing["section"] = "missing_summary"
        combined = pd.concat([report, missing], ignore_index=True, sort=False)
        write_table(combined, path, output_format, "rule_report")
        return
    raise BuildError(f"Unsupported rule_report_format: {output_format}")


def build_sync_entries(rows: list[dict[str, Any]], manifest_path: Path) -> list[dict[str, Any]]:
    entries = []
    for row in rows:
        if row["status"] != "success":
            continue
        entries.append(
            {
                "label": row["panel_id"],
                "asset_root": row["panel_path"],
                "enabled": True,
                "source_type": "panel_builder_output",
                "origin_label": row["panel_id"],
                "panel_id": row["panel_id"],
                "panel_group": row["panel_group"],
                "panel_grain": row["panel_grain"],
                "y_id": row["y_id"],
                "x_id": row["x_id"],
                "c_bundle_id": row["c_bundle_id"],
                "builder_manifest": str(manifest_path),
                "provider_id": row["provider_id"]
            }
        )
    return entries


def run_build(spec: dict[str, Any]) -> dict[str, Any]:
    paths = build_output_paths(spec["case_root"])
    ensure_dirs(paths)
    combos = expand_combos(spec)
    rows: list[dict[str, Any]] = []
    output_format = spec["output_policy"]["output_format"]
    rule_report_format = spec["output_policy"]["rule_report_format"]
    exceptions_format = spec["output_policy"]["exceptions_format"]
    suffix = ".csv" if output_format == "csv" else ".xlsx"
    rule_report_suffix = ".csv" if rule_report_format == "csv" else ".xlsx"
    exceptions_suffix = ".csv" if exceptions_format == "csv" else ".xlsx"

    for combo in combos:
        panel_id = make_panel_id(combo, spec["output_policy"]["naming_pattern"])
        panel_path = paths["panel_dir"] / f"{panel_id}{suffix}"
        rule_report_path = paths["rule_report_dir"] / f"{panel_id}_规则报告{rule_report_suffix}"
        exceptions_path = paths["exception_dir"] / f"{panel_id}_exceptions{exceptions_suffix}"
        row = {
            "panel_id": panel_id,
            "panel_group": combo.panel_group,
            "panel_grain": combo.panel_grain,
            "key_template": combo.key_template,
            "y_id": combo.y_var["id"],
            "x_id": combo.x_var["id"],
            "c_bundle_id": combo.c_bundle["id"],
            "status": "failed",
            "panel_path": None,
            "rule_report_path": str(rule_report_path),
            "exceptions_path": str(exceptions_path),
            "exception_count": 0,
            "non_missing_summary": {},
            "synced_to_regression": False,
            "provider_id": combo.y_var["provider_id"]
        }
        try:
            panel, missing_summary = build_panel_for_combo(combo, spec)
            write_panel(panel, panel_path, output_format)
            write_rule_report(rule_report_path, combo, missing_summary, rule_report_format)
            write_table(build_exception_frame(""), exceptions_path, exceptions_format, "exceptions")
            row["status"] = "success"
            row["panel_path"] = str(panel_path)
            row["non_missing_summary"] = {
                item["column"]: round(1 - item["missing_rate"], 6)
                for item in missing_summary.to_dict(orient="records")
            }
        except Exception as error:
            write_table(build_exception_frame(str(error)), exceptions_path, exceptions_format, "exceptions")
            row["exception_count"] = 1
            row["error_message"] = str(error)
        rows.append(row)

    manifest_path = paths["manifest_dir"] / "panel_manifest.json"
    manifest_xlsx_path = paths["manifest_dir"] / "panel_manifest.xlsx"
    manifest_payload = {
        "output_policy": spec["output_policy"],
        "panel_count": len(rows),
        "success_count": sum(1 for row in rows if row["status"] == "success"),
        "panels": rows
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_xlsx(pd.DataFrame(rows), manifest_xlsx_path, "panel_manifest")

    sync_path = None
    if spec["output_policy"]["sync_to_regression"] and {
        "regression_data_manifest",
        "regression_data_manifest",
    }.intersection(spec["sync_targets"]):
        entries = build_sync_entries(rows, manifest_path)
        paths["sync_manifest"].write_text(json.dumps({"sources": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
        sync_path = str(paths["sync_manifest"])
        for row in rows:
            if row["status"] == "success":
                row["synced_to_regression"] = True
        manifest_path.write_text(json.dumps({**manifest_payload, "panels": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        write_xlsx(pd.DataFrame(rows), manifest_xlsx_path, "panel_manifest")

    return {
        "manifest_path": str(manifest_path),
        "manifest_xlsx_path": str(manifest_xlsx_path),
        "panel_count": len(rows),
        "success_count": sum(1 for row in rows if row["status"] == "success"),
        "sync_data_sources_path": sync_path
    }


def main() -> None:
    args = parse_args()
    result = run_build(load_and_expand_spec(args.spec_file))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
