from __future__ import annotations

import json
import math
import os
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from skill_workspace import OUTPUT_RESULTS_DIR, OUTPUT_RESULTS_FIGURES_DIR, OUTPUT_RESULTS_FOLLOWUPS_DIR, OUTPUT_RESULTS_LOGS_DIR, OUTPUT_RESULTS_SUMMARIES_DIR, OUTPUT_RESULTS_TABLES_DIR, OUTPUT_RUNTIME_LOGS_DIR, OUTPUT_RUNTIME_TMP_DIR, ROOT, ensure_workspace_dirs, reset_for_new_project, save_json
    from stata_skill_workflow import DEFAULT_DO_PATH, DEFAULT_SPEC_PATH, FIGURE_DIR, LOG_DIR, SPEC_DIR, TABLE_DIR, ensure_skill_output_dirs, write_default_workflow_artifacts
except ModuleNotFoundError:
    from scripts.skill_workspace import OUTPUT_RESULTS_DIR, OUTPUT_RESULTS_FIGURES_DIR, OUTPUT_RESULTS_FOLLOWUPS_DIR, OUTPUT_RESULTS_LOGS_DIR, OUTPUT_RESULTS_SUMMARIES_DIR, OUTPUT_RESULTS_TABLES_DIR, OUTPUT_RUNTIME_LOGS_DIR, OUTPUT_RUNTIME_TMP_DIR, ROOT, ensure_workspace_dirs, reset_for_new_project, save_json
    from scripts.stata_skill_workflow import DEFAULT_DO_PATH, DEFAULT_SPEC_PATH, FIGURE_DIR, LOG_DIR, SPEC_DIR, TABLE_DIR, ensure_skill_output_dirs, write_default_workflow_artifacts


def find_stata_executable() -> Path:
    candidates = []
    env_path = os.environ.get("REGRESSION_STATA_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("D:/Stata17/StataMP-64.exe"),
            Path("D:/Stata17/stata.exe"),
            Path("C:/Program Files/Stata18/StataMP-64.exe"),
            Path("C:/Program Files/Stata17/StataMP-64.exe"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError("没有找到可用的 Stata 可执行文件。")


def stata_path_text(path: Path) -> str:
    return str(path).replace("\\", "/")


def stata_plus_dir(stata_path: Path) -> Path:
    return stata_path.parent / "ado" / "plus"


def stata_personal_dir(stata_path: Path) -> Path:
    return stata_path.parent / "ado" / "personal"


def stata_string_list(values: list[str]) -> str:
    return " ".join(str(item) for item in values if item)


def clean_module_stub(text: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text)
    return safe.strip("_") or "module"


def factor_term(term: str) -> str:
    if "#" in term:
        return "#".join(f"i.{part}" for part in term.split("#"))
    return f"i.{term}"


def analysis_plan(spec: dict[str, Any]) -> dict[str, Any]:
    return dict(spec.get("analysis_plan") or {})


def analysis_lines(spec: dict[str, Any]) -> list[dict[str, Any]]:
    plan = analysis_plan(spec)
    return list(plan.get("analysis_lines") or spec.get("analysis_lines") or [])


def package_requirements(spec: dict[str, Any]) -> list[str]:
    plan = analysis_plan(spec)
    return [str(item) for item in plan.get("package_requirements") or spec.get("package_requirements") or []]


def has_models(spec: dict[str, Any]) -> bool:
    return any(module.get("models") for line in analysis_lines(spec) for module in line.get("modules", []))


def build_model_command(model: dict[str, Any]) -> str:
    estimator = str(model["estimator"])
    depvar = str(model["depvar"])
    regressors = stata_string_list([str(item) for item in model.get("regressors", [])])
    absorb = stata_string_list([str(item) for item in model.get("absorb", [])])
    cluster = stata_string_list([str(item) for item in model.get("cluster", [])])
    options = stata_string_list([str(item) for item in model.get("options", [])])
    panel_settings = dict(model.get("panel_settings") or {})
    option_parts: list[str] = []
    if absorb and estimator in {"reghdfe", "ivreghdfe", "ppmlhdfe"}:
        option_parts.append(f"absorb({absorb})")
    if cluster:
        if estimator in {"reghdfe", "ivreghdfe", "ppmlhdfe"}:
            option_parts.append(f"cluster({cluster})")
        else:
            option_parts.append(f"vce(cluster {cluster})")
    if options:
        option_parts.append(options)
    option_text = ", " + " ".join(option_parts) if option_parts else ""
    if estimator == "ivreghdfe":
        endogenous = str(model["iv_endogenous"])
        instruments = stata_string_list([str(item) for item in model.get("iv_instruments", [])])
        rhs = f"({endogenous} = {instruments})"
        if regressors:
            rhs = f"{rhs} {regressors}"
        return f"{estimator} {depvar} {rhs}{option_text}"
    if estimator == "csdid":
        ivar = str(model["ivar"])
        timevar = str(model["timevar"])
        gvar = str(model["gvar"])
        rhs = stata_string_list([depvar, regressors]).strip()
        option_text = f", ivar({ivar}) time({timevar}) gvar({gvar})"
        if options:
            option_text = f"{option_text} {options}"
        return f"csdid {rhs}{option_text}"
    if estimator == "xttobit":
        option_text = ", " + options if options else ""
        return f"xttobit {depvar} {regressors}{option_text}".strip()
    if estimator == "xtnbreg":
        xt_options = [options] if options else []
        if panel_settings.get("fe") and "fe" not in xt_options:
            xt_options.append("fe")
        option_text = ", " + " ".join(item for item in xt_options if item) if xt_options else ""
        return f"xtnbreg {depvar} {regressors}{option_text}".strip()
    return f"{estimator} {depvar} {regressors}{option_text}".strip()


def default_csdid_event_terms() -> list[str]:
    return ["Pre_avg", "Post_avg", "Tm5", "Tm4", "Tm3", "Tm2", "Tm1", "Tp0", "Tp1", "Tp2", "Tp3", "Tp4", "Tp5"]


def package_install_commands(package: str) -> list[str]:
    if package == "reghdfe":
        return ['capture ssc install require, replace', "capture ssc install ftools, replace", "capture ssc install reghdfe, replace"]
    if package == "ivreghdfe":
        return ['capture ssc install require, replace', "capture ssc install ivreg2, replace", "capture ssc install ranktest, replace", "capture ssc install ftools, replace", "capture ssc install reghdfe, replace", "capture ssc install ivreghdfe, replace"]
    if package == "estout":
        return ["capture ssc install estout, replace"]
    if package == "ppmlhdfe":
        return ["capture ssc install ftools, replace", "capture ssc install reghdfe, replace", "capture ssc install ppmlhdfe, replace"]
    if package == "drdid":
        return ['capture net install drdid, from("http://fmwww.bc.edu/RePEc/bocode/d") replace', "capture ssc install drdid, replace"]
    if package == "csdid":
        return ['capture net install drdid, from("http://fmwww.bc.edu/RePEc/bocode/d") replace', 'capture net install csdid, from("http://fmwww.bc.edu/RePEc/bocode/c") replace', "capture ssc install drdid, replace", "capture ssc install csdid, replace"]
    if package == "psmatch2":
        return ["capture ssc install psmatch2, replace"]
    return [f"capture ssc install {package}, replace"]


def build_sample_filter_lines(filters: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in filters:
        if item.get("type") == "range":
            lines.append(f'keep if inrange({item["column"]}, {item["min"]}, {item["max"]})')
        elif item.get("type") == "exclude_equals":
            value = item["value"]
            value_text = f'"{value}"' if isinstance(value, str) else str(value)
            lines.append(f"drop if {item['column']} == {value_text}")
    return lines


def add_standard_result_capture(lines: list[str], line_id: str, module_type: str, module_name: str, label: str, estimator: str, depvar: str, focus_terms: list[str]) -> None:
    lines.extend(
        [
            "local ok = (`rc' == 0)",
            "local nobs = .",
            "local r2 = .",
            'local error_type ""',
            'local error_message ""',
            "if `ok' == 1 {",
            "    capture local nobs = e(N)",
            "    capture scalar __r2 = e(r2_a)",
            "    if _rc capture scalar __r2 = e(r2)",
            "    if _rc capture scalar __r2 = e(r2_p)",
            "    if _rc scalar __r2 = .",
            "    local r2 = __r2",
            "}",
            "else {",
            '    local error_type "estimation_failed"',
            '    local error_message "模型执行失败，请看 output/runtime/logs/execution.log 和 rc。"',
            f"    post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (`\"`error_type'\"') (`\"`error_message'\"') (`rc')",
            "}",
        ]
    )
    for term in focus_terms:
        term_text = str(term).replace('"', "'")
        term_lines = [
            "local coef = .",
            "local se = .",
            "local pval = .",
            'local pvalue_source "missing"',
            "if `ok' == 1 {",
            "    capture matrix __rtab = r(table)",
            "    if _rc == 0 {",
            f"        local __term_col = colnumb(__rtab, \"{term_text}\")",
            "        if missing(`__term_col') == 0 {",
            "            capture scalar __b_from_table = el(__rtab, 1, `__term_col')",
            "            capture scalar __se_from_table = el(__rtab, 2, `__term_col')",
            "            capture scalar __p_from_table = el(__rtab, 4, `__term_col')",
            "            if _rc == 0 {",
            "                local coef = __b_from_table",
            "                local se = __se_from_table",
            "                if missing(__p_from_table) == 0 {",
            "                    local pval = __p_from_table",
            '                    local pvalue_source "direct_table"',
            "                }",
            "            }",
            "        }",
            "    }",
            "}",
        ]
        term_lines.extend(
            [
                "if `ok' == 1 & missing(`coef') {",
                f"    capture scalar __b = _b[{term_text}]",
                "    if _rc == 0 {",
                f"        capture scalar __se = _se[{term_text}]",
                "        if _rc == 0 {",
                "            local coef = __b",
                "            local se = __se",
                "            if _rc == 0 & missing(`pval') {",
                "                if missing(__se) == 0 & __se != 0 {",
                "                    capture scalar __df = e(df_r)",
                "                    if _rc == 0 & missing(__df) == 0 {",
                "                        local pval = 2 * ttail(__df, abs(__b / __se))",
                '                        local pvalue_source "t_df_r"',
                "                    }",
                "                    else {",
                "                        local pval = 2 * normal(-abs(__b / __se))",
                '                        local pvalue_source "z_normal"',
                "                    }",
                "                }",
                "            }",
                "        }",
                "    }",
                "}",
            ]
        )
        term_lines.extend(
            [
                "if `ok' == 1 & missing(`coef') {",
                f"    post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"result_term_missing\") (\"目标项没有出现在模型返回结果里。\") (.)",
                "}",
                "if `ok' == 1 & missing(`coef') == 0 & missing(`se') {",
                f"    post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"standard_error_missing\") (\"目标项拿到了系数，但标准误缺失。\") (.)",
                "}",
                "if `ok' == 1 & missing(`coef') == 0 & missing(`se') == 0 & missing(`pval') {",
                f"    post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"pvalue_missing\") (\"目标项拿到了系数和标准误，但 p 值缺失。\") (.)",
                "}",
            ]
        )
        term_lines.append(
            f"post modelpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"{estimator}\") (\"{depvar}\") (\"{term_text}\") (`ok') (`nobs') (`r2') (`coef') (`se') (`pval') (`\"`pvalue_source'\"') (`rc') (`\"`error_type'\"') (`\"`error_message'\"')"
        )
        lines.extend(term_lines)
    lines.extend(
        [
            "if `ok' == 1 {",
            "    if missing(`nobs') | `nobs' < 30 {",
            f"post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"small_sample\") (\"有效样本量过小，先别直接相信结果。\") (`nobs')",
            "    }",
            "    if missing(`r2') {",
            f"post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"missing_r2\") (\"这个模型没有稳定返回 R2，可能和估计方法有关。\") (.)",
            "    }",
            "}",
        ]
    )


def build_post_estimation_lines(line_id: str, module_type: str, module_name: str, label: str, estimator: str, model: dict[str, Any]) -> list[str]:
    cfg = dict(model.get("post_estimation") or {})
    if not cfg:
        return []
    lines: list[str] = []
    if estimator == "csdid" and cfg.get("type") == "csdid_plot":
        plot_stub = clean_module_stub(f"{line_id}_{module_name}_csdid_event")
        figure_path_zh = stata_path_text(OUTPUT_RESULTS_FIGURES_DIR / "zh" / f"{plot_stub}.png")
        figure_path_en = stata_path_text(OUTPUT_RESULTS_FIGURES_DIR / "en" / f"{plot_stub}.png")
        xlabel = str(cfg.get("xlabel") or "-5(1)5")
        yline = str(cfg.get("yline") or "0")
        title = str(cfg.get("title") or "政策对结果变量的动态效应")
        lines.extend(
            [
                "if `ok' == 1 {",
                f"    capture noisily csdid_plot, xlabel({xlabel}) yline({yline}) title(\"{title}\") name(csdid_event_plot, replace)",
                "    if _rc == 0 {",
                f"        graph export \"{figure_path_zh}\", replace",
                f"        graph export \"{figure_path_en}\", replace",
                f"        post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"event_plot_exported\") (\"已导出交错 DID 事件研究图。\") (1)",
                "    }",
                "    else {",
                f"        post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"event_plot_failed\") (\"csdid 已跑完，但事件研究图没有成功导出。\") (.)",
                "    }",
                "}",
            ]
        )
    return lines


def build_parallel_trends_lines(line_id: str, line_spec: dict[str, Any]) -> list[str]:
    cfg = dict(line_spec.get("parallel_trends", {}))
    if not cfg.get("enabled"):
        return []
    depvar = str(cfg.get("depvar", "patent_new"))
    gvar = str(line_spec.get("did", {}).get("gvar", "policy_year"))
    controls = stata_string_list([str(item) for item in cfg.get("controls", [])])
    absorb = stata_string_list([str(item) for item in cfg.get("absorb", [])])
    cluster = stata_string_list([str(item) for item in cfg.get("cluster", []) or ["id"]])
    baseline = int(cfg.get("baseline", -1))
    leads = int(cfg.get("leads", 4))
    lags = int(cfg.get("lags", 4))
    figure_path_zh = stata_path_text(OUTPUT_RESULTS_FIGURES_DIR / "zh" / f"{clean_module_stub(line_id)}_parallel_trends.png")
    figure_path_en = stata_path_text(OUTPUT_RESULTS_FIGURES_DIR / "en" / f"{clean_module_stub(line_id)}_parallel_trends.png")
    lines = [
        "preserve",
        f"gen __event_time = year - {gvar}",
        f"replace __event_time = . if missing({gvar})",
        f"replace __event_time = -{leads} if __event_time < -{leads} & !missing(__event_time)",
        f"replace __event_time = {lags} if __event_time > {lags} & !missing(__event_time)",
        f"gen __event_slot = __event_time + {leads + 1} if !missing(__event_time)",
        f"capture noisily reghdfe {depvar} ib{baseline + leads + 1}.__event_slot {controls}, absorb({absorb}) cluster({cluster})",
        "local rc = _rc",
    ]
    pre_terms = [f"{k + leads + 1}.__event_slot" for k in range(-leads, 0) if k != baseline]
    post_terms = [f"{k + leads + 1}.__event_slot" for k in range(0, lags + 1)]
    add_standard_result_capture(lines, line_id, "parallel_trends", "event_study", "event_study", "reghdfe", depvar, [*pre_terms, *post_terms])
    test_terms = " ".join(pre_terms)
    plot_fill_lines: list[str] = []
    for k in range(-leads, lags + 1):
        row = k + leads + 1
        if k == baseline:
            continue
        slot = k + leads + 1
        plot_fill_lines.extend(
            [
                f"    capture replace coef = _b[{slot}.__event_slot] in {row}",
                f"    capture replace se = _se[{slot}.__event_slot] in {row}",
            ]
        )
    lines.extend(
        [
            "if `ok' == 1 {",
            f"    capture test {test_terms}",
            "    if _rc == 0 {",
            f"        post qualpost (\"{line_id}\") (\"parallel_trends\") (\"event_study\") (\"event_study\") (\"pretrend_pvalue\") (\"平行趋势联合检验 p 值。\") (r(p))",
            "    }",
            "    clear",
            f"    set obs {leads + lags + 1}",
            f"    gen event_time = _n - {leads + 1}",
            "    gen coef = .",
            "    gen se = .",
            *plot_fill_lines,
            "    gen lb = coef - 1.96 * se",
            "    gen ub = coef + 1.96 * se",
            "    twoway (rcap lb ub event_time) (scatter coef event_time) (line coef event_time), xline(-1, lpattern(dash)) yline(0, lpattern(dash)) xtitle(\"事件期\") ytitle(\"系数\") title(\"平行趋势检验\") legend(off)",
            f"    graph export \"{figure_path_zh}\", replace",
            f"    graph export \"{figure_path_en}\", replace",
            "}",
            "restore",
        ]
    )
    return lines


def build_psm_did_lines(line_id: str, line_spec: dict[str, Any]) -> list[str]:
    cfg = dict(line_spec.get("matching", {}))
    if not cfg.get("enabled"):
        return []
    depvar = str(cfg.get("did_depvar", "patent_new"))
    treatment = str(cfg.get("treatment_column", "did"))
    covars = stata_string_list([str(item) for item in cfg.get("covariates", [])])
    absorb = stata_string_list([str(item) for item in cfg.get("did_absorb", [])])
    cluster = stata_string_list([str(item) for item in cfg.get("did_cluster", []) or ["id"]])
    neighbors = int(cfg.get("neighbors", 1))
    caliper = cfg.get("caliper", 0.05)
    common = "common" if cfg.get("common_support", True) else ""
    noreplacement = "" if cfg.get("replacement", True) else "noreplacement"
    lines = [
        "preserve",
        "capture which psmatch2",
        "if _rc != 0 {",
        "    capture ssc install psmatch2, replace",
        "}",
        "bysort id: egen __first_treat_year = min(policy_year)",
        "gen __ever_treated = !missing(__first_treat_year)",
        "gen __match_year = __first_treat_year - 1 if __ever_treated == 1",
        "bysort year: egen __treated_in_match_year = max(year == __match_year & __ever_treated == 1)",
        "replace __treated_in_match_year = 0 if missing(__treated_in_match_year)",
        "gen __match_sample = 0",
        "replace __match_sample = 1 if __ever_treated == 1 & year == __match_year",
        "replace __match_sample = 1 if __treated_in_match_year == 1 & (__ever_treated == 0 | __first_treat_year > year)",
        "capture count if __match_sample == 1 & __ever_treated == 1",
        f'post qualpost ("{line_id}") ("psm_did") ("psm_did_core") ("psm_did") ("matched_treated_preperiod_n") ("进入处理前一期匹配池的未来处理组样本量。") (r(N))',
        "capture count if __match_sample == 1 & (__ever_treated == 0 | __first_treat_year > year)",
        f'post qualpost ("{line_id}") ("psm_did") ("psm_did_core") ("psm_did") ("matched_control_candidate_n") ("进入匹配池且到当年仍未处理的对照候选样本量。") (r(N))',
        f'post qualpost ("{line_id}") ("psm_did") ("psm_did_core") ("psm_did") ("matching_rule") ("匹配池按处理前一期的未来处理组，配同一年仍未处理的样本；已经在当年及以前处理过的样本不会进对照组。") (.)',
        f"capture noisily psmatch2 __ever_treated {covars} if __match_sample == 1, logit neighbor({neighbors}) caliper({caliper}) {common} {noreplacement}",
        "local rc = _rc",
        "if `rc' == 0 {",
        "    gen __matched_keep = (_support == 1) if !missing(_support)",
        "    bysort id: egen __matched_id = max(__matched_keep)",
        f"    capture noisily reghdfe {depvar} {treatment} {covars} if __matched_id == 1, absorb({absorb}) cluster({cluster})",
        "    local rc = _rc",
        "}",
    ]
    add_standard_result_capture(lines, line_id, "psm_did", "psm_did_core", "psm_did", "reghdfe", depvar, [treatment], False)
    lines.extend(
        [
            "if `ok' == 1 {",
            f"    post qualpost (\"{line_id}\") (\"psm_did\") (\"psm_did_core\") (\"psm_did\") (\"matching_design\") (\"PSM-DID 使用处理前一期样本、logit、1:1 最近邻、common support、允许放回、caliper(0.05)。\") ({neighbors})",
            "}",
            "restore",
        ]
    )
    return lines


def build_placebo_lines(line_id: str, line_spec: dict[str, Any]) -> list[str]:
    cfg = dict(line_spec.get("placebo", {}))
    if not cfg.get("enabled"):
        return []
    depvar = str(cfg.get("depvar", "patent_new"))
    controls = stata_string_list([str(item) for item in cfg.get("controls", [])])
    absorb = stata_string_list([str(item) for item in cfg.get("absorb", [])])
    cluster = stata_string_list([str(item) for item in cfg.get("cluster", []) or ["id"]])
    reps = int(cfg.get("reps", 500))
    seed = int(cfg.get("seed", 20260322))
    lines = [
        "preserve",
        f"set seed {seed}",
        "tempfile original_policy shuffled_policy placebo_results",
        "postfile __placebopost double iter coef using `placebo_results', replace",
        "keep if !missing(policy_year)",
        "keep id policy_year",
        "duplicates drop",
        "gen __row = _n",
        "save `original_policy'",
        "restore",
        f"forvalues r = 1/{reps} {{",
        "    preserve",
        "    use `original_policy', clear",
        "    gen __u = runiform()",
        "    sort __u",
        "    replace __row = _n",
        "    keep __row policy_year",
        "    rename policy_year __shuffled_policy_year",
        "    save `shuffled_policy', replace",
        "    restore",
        "    preserve",
        "    merge m:1 id using `original_policy', nogen keep(master match)",
        "    merge m:1 __row using `shuffled_policy', nogen keep(master match)",
        "    gen placebo_did = (year >= __shuffled_policy_year) if !missing(__shuffled_policy_year)",
        "    replace placebo_did = 0 if missing(placebo_did)",
        "    local __rc = .",
        f"    capture quietly reghdfe {depvar} placebo_did {controls}, absorb({absorb}) cluster({cluster})",
        "    local __rc = _rc",
        "    if `__rc' == 0 {",
        "        capture post __placebopost (`r') (_b[placebo_did])",
        "    }",
        "    restore",
        "}",
        "postclose __placebopost",
        "use `placebo_results', clear",
        "summ coef, detail",
        f'post qualpost ("{line_id}") ("placebo") ("shuffle_policy_year") ("shuffle_policy_year") ("placebo_median") ("随机打乱 policy_year 的 placebo 系数中位数。") (r(p50))',
        f'post qualpost ("{line_id}") ("placebo") ("shuffle_policy_year") ("shuffle_policy_year") ("placebo_p975") ("随机打乱 policy_year 的 placebo 系数 97.5 分位数。") (r(p975))',
        f'export delimited using "{stata_path_text(LOG_DIR / "placebo_shuffle_policy_year.csv")}", replace',
        f'use "{stata_path_text(ROOT / "data" / str(line_spec["data_file"]))}", clear',
        f"capture noisily reghdfe {depvar} did {controls}, absorb({absorb}) cluster({cluster})",
        "local rc = _rc",
    ]
    add_standard_result_capture(lines, line_id, "placebo", "shuffle_policy_year", "actual_did", "reghdfe", depvar, ["did"])
    lines.append(f'post qualpost ("{line_id}") ("placebo") ("shuffle_policy_year") ("actual_did") ("placebo_reps") ("本次随机打乱 policy_year 的重复次数。") ({reps})')
    return lines


def build_dynamic_do(spec: dict[str, Any], do_path: Path) -> None:
    package_requirement_list = package_requirements(spec)
    stata_path = find_stata_executable()
    plus_dir = stata_plus_dir(stata_path)
    personal_dir = stata_personal_dir(stata_path)
    lines: list[str] = [
        "version 17.0",
        "clear all",
        "set more off",
        "capture log close",
        f'log using "{stata_path_text(OUTPUT_RUNTIME_LOGS_DIR / "execution.log")}", replace text',
        f'capture mkdir "{stata_path_text(plus_dir)}"',
        f'capture mkdir "{stata_path_text(personal_dir)}"',
        f'sysdir set PLUS "{stata_path_text(plus_dir)}"',
        f'sysdir set PERSONAL "{stata_path_text(personal_dir)}"',
        "tempfile pkgstatus modelstatus qualitystatus",
        "postfile pkgpost str32 package byte installed byte install_attempted byte install_succeeded using `pkgstatus', replace",
    ]
    for package in package_requirement_list:
        install_lines = package_install_commands(package)
        lines.extend([f"capture which {package}", "local installed = (_rc == 0)", "local attempted = 0", "local succeeded = 0"])
        if package == "ivreghdfe":
            lines.extend(["local attempted = 1", "if 1 == 1 {"])
        else:
            lines.extend(["if `installed' == 0 {", "    local attempted = 1"])
        for install_line in install_lines:
            lines.append(f"    {install_line}")
        lines.extend(
            [
                f"    capture which {package}",
                "    if _rc == 0 {",
                "        local succeeded = 1",
                "        local installed = 1",
                "    }",
                "}",
                f"post pkgpost (\"{package}\") (`installed') (`attempted') (`succeeded')",
            ]
        )
    lines.extend(
        [
            "postclose pkgpost",
            "use `pkgstatus', clear",
            f'export delimited using "{stata_path_text(LOG_DIR / "package_status.csv")}", replace',
            "postfile modelpost str24 analysis_line str24 module_type str48 module_name str24 model_label str24 estimator str64 depvar str80 focus_term byte ok double nobs r2 coef se pvalue str24 pvalue_source double error_code str32 error_type str200 error_message using `modelstatus', replace",
            "postfile qualpost str24 analysis_line str24 module_type str48 module_name str24 model_label str32 check_name str200 message double check_value using `qualitystatus', replace",
        ]
    )
    for line_spec in analysis_lines(spec):
        line_id = str(line_spec["line_id"])
        data_file = ROOT / "data" / str(line_spec["data_file"])
        lines.append(f'use "{stata_path_text(data_file)}", clear')
        lines.extend(
            [
                "capture noisily duplicates tag _all, gen(__dup_all)",
                "capture count if __dup_all > 0",
                "local __dup_all_n = r(N)",
                "if `__dup_all_n' > 0 {",
                "    quietly duplicates drop _all, force",
                f"    post qualpost (\"{line_id}\") (\"prep\") (\"dedup\") (\"prep\") (\"exact_duplicate_rows_dropped\") (\"发现整行完全重复记录，已在执行前自动去重。\") (`__dup_all_n')",
                "}",
                "capture drop __dup_all",
            ]
        )
        lines.extend(build_sample_filter_lines(list(line_spec.get("sample_filters", []))))
        if line_spec.get("winsorize", {}).get("enabled"):
            lines.append(f"post qualpost (\"{line_id}\") (\"prep\") (\"winsorize\") (\"prep\") (\"winsorize_skipped\") (\"当前版本先保留缩尾设定到 spec，未在 do-file 里自动改数据。\") (.)")
        for module in line_spec.get("modules", []):
            module_type = str(module["module_type"])
            module_name = str(module["name"])
            for model in module.get("models", []):
                label = str(model["label"])
                estimator = str(model["estimator"])
                depvar = str(model["depvar"])
                command = build_model_command(model)
                lines.extend(["local rc = ."])
                panel_settings = dict(model.get("panel_settings") or {})
                panel_id = str(panel_settings.get("id") or "")
                panel_time = str(panel_settings.get("time") or "")
                if estimator.startswith("xt") and panel_id and panel_time:
                    lines.append(f"capture noisily xtset {panel_id} {panel_time}")
                if estimator in {"reghdfe", "ivreghdfe", "ppmlhdfe", "csdid", "psmatch2"}:
                    lines.extend(
                        [
                            f"capture which {estimator}",
                            "if _rc != 0 {",
                            "    local rc = 199",
                            f"    post qualpost (\"{line_id}\") (\"{module_type}\") (\"{module_name}\") (\"{label}\") (\"package_missing\") (\"当前模型依赖的命令没有装好。\") (`rc')",
                            "}",
                            "else {",
                            f"    capture noisily {command}",
                            "    local rc = _rc",
                            "}",
                        ]
                    )
                else:
                    lines.extend([f"capture noisily {command}", "local rc = _rc"])
                add_standard_result_capture(lines, line_id, module_type, module_name, label, estimator, depvar, list(model.get("focus_terms", [])))
                lines.extend(build_post_estimation_lines(line_id, module_type, module_name, label, estimator, model))
        if line_spec.get("did", {}).get("enabled") and line_spec.get("did", {}).get("gvar"):
            gvar = str(line_spec["did"]["gvar"])
            lines.extend([f"capture count if !missing({gvar})", f"post qualpost (\"{line_id}\") (\"did\") (\"did_design\") (\"design\") (\"gvar_nonmissing\") (\"处理时点非缺失样本量\") (r(N))"])
        lines.extend(build_parallel_trends_lines(line_id, line_spec))
        lines.extend(build_psm_did_lines(line_id, line_spec))
        lines.extend(build_placebo_lines(line_id, line_spec))
    lines.extend(["postclose modelpost", "postclose qualpost", "use `modelstatus', clear", f'export delimited using "{stata_path_text(LOG_DIR / "model_results.csv")}", replace', "use `qualitystatus', clear", f'export delimited using "{stata_path_text(LOG_DIR / "quality_checks.csv")}", replace', "log close"])
    do_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_module_tables() -> None:
    results_path = LOG_DIR / "model_results.csv"
    if not results_path.exists():
        return
    frame = pd.read_csv(results_path, encoding="utf-8-sig")
    if frame.empty:
        return
    for keys, module_frame in frame.groupby(["analysis_line", "module_type", "module_name"], dropna=False):
        analysis_line, _, module_name = keys
        file_name = f"{clean_module_stub(str(analysis_line))}_{clean_module_stub(str(module_name))}.csv"
        module_frame.to_csv(TABLE_DIR / "zh" / file_name, index=False, encoding="utf-8-sig")
        module_frame.to_csv(TABLE_DIR / "en" / file_name, index=False, encoding="utf-8-sig")


def module_display_name(module_stub: str) -> str:
    mapping = {
        "iv_only": ("工具变量回归", "IV Regression"),
        "baseline_core": ("基准回归", "Baseline Regression"),
        "market_information": ("机制检验", "Mechanism Analysis"),
        "robustness_core": ("稳健性检验", "Robustness Checks"),
        "heterogeneity_core": ("异质性检验", "Heterogeneity Analysis"),
        "did_core": ("DID 检验", "DID Analysis"),
        "event_study": ("平行趋势检验", "Event Study"),
        "psm_did_core": ("PSM-DID 检验", "PSM-DID Analysis"),
        "shuffle_policy_year": ("安慰剂检验", "Placebo Test"),
    }
    return mapping.get(module_stub, (module_stub.replace("_", " "), module_stub.replace("_", " ").title()))


def expected_module_figure_items(line_id: str, module_name: str) -> list[dict[str, str]]:
    if module_name == "event_study":
        file_name = f"{clean_module_stub(line_id)}_parallel_trends.png"
        return [
            {
                "file_zh": f"results/figures/zh/{file_name}",
                "file_en": f"results/figures/en/{file_name}",
                "title": "平行趋势图",
                "title_en": "Parallel Trends Plot",
                "description": "这一部分展示事件研究的动态系数图，用来看处理前趋势和处理后变化。",
                "description_en": "This figure shows the event-study coefficients for checking pre-trends and post-treatment dynamics.",
                "note": "注：虚线位置是基准期，点和误差棒展示各事件期系数及其置信区间。",
                "note_en": "Notes: The dashed line marks the base period, and the points with error bars show event-time coefficients and confidence intervals.",
            }
        ]
    if "csdid_event" in module_name:
        file_name = f"{clean_module_stub(f'{line_id}_{module_name}_csdid_event')}.png"
        return [
            {
                "file_zh": f"results/figures/zh/{file_name}",
                "file_en": f"results/figures/en/{file_name}",
                "title": "交错 DID 事件研究图",
                "title_en": "Staggered DID Event-Study Plot",
                "description": "这一部分展示 csdid 的动态处理效应图，用来看政策前后各期效应变化。",
                "description_en": "This figure shows the csdid dynamic treatment effects across event time.",
                "note": "注：这是基于 csdid 的事件期聚合结果自动绘制的动态效应图。",
                "note_en": "Notes: This plot is automatically generated from csdid event-time aggregation.",
            }
        ]
    return []


def build_report_config(spec: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for line_spec in analysis_lines(spec):
        line_id = str(line_spec["line_id"])
        line_title = str(line_spec.get("title") or line_id)
        for module in line_spec.get("modules", []):
            module_name = str(module["name"])
            file_name = f"{clean_module_stub(line_id)}_{clean_module_stub(module_name)}.csv"
            zh_path = OUTPUT_RESULTS_TABLES_DIR / "zh" / file_name
            en_path = OUTPUT_RESULTS_TABLES_DIR / "en" / file_name
            if not zh_path.exists() or not en_path.exists():
                missing = []
                if not zh_path.exists():
                    missing.append(str(zh_path))
                if not en_path.exists():
                    missing.append(str(en_path))
                raise FileNotFoundError(f"报告缺少模块表，不能继续生成：{'; '.join(missing)}")
            title_zh, title_en = module_display_name(module_name)
            items.append(
                {
                    "type": "table",
                    "file_zh": f"results/tables/zh/{file_name}",
                    "file_en": f"results/tables/en/{file_name}",
                    "title": f"{line_title}：{title_zh}",
                    "title_en": f"{line_title}: {title_en}",
                    "note": "注：这是按当前任务设定自动导出的模块结果表。",
                    "note_en": "Notes: This table is automatically generated for the current task module.",
                    "description": f"这一部分展示 {line_title} 的 {title_zh} 结果。",
                    "description_en": f"This section reports the {title_en.lower()} for {line_title}.",
                }
            )
            for figure_item in expected_module_figure_items(line_id, module_name):
                zh_figure_path = OUTPUT_RESULTS_DIR.parent / str(figure_item["file_zh"])
                en_figure_path = OUTPUT_RESULTS_DIR.parent / str(figure_item["file_en"])
                if not zh_figure_path.exists() or not en_figure_path.exists():
                    missing = []
                    if not zh_figure_path.exists():
                        missing.append(str(zh_figure_path))
                    if not en_figure_path.exists():
                        missing.append(str(en_figure_path))
                    raise FileNotFoundError(f"报告缺少模块图，不能继续生成：{'; '.join(missing)}")
                items.append(
                    {
                        "type": "figure",
                        "file_zh": figure_item["file_zh"],
                        "file_en": figure_item["file_en"],
                        "title": f"{line_title}：{figure_item['title']}",
                        "title_en": f"{line_title}: {figure_item['title_en']}",
                        "note": figure_item["note"],
                        "note_en": figure_item["note_en"],
                        "description": figure_item["description"],
                        "description_en": figure_item["description_en"],
                    }
                )
    return {
        "title": str(spec.get("project_title") or "回归分析报告"),
        "title_en": str(spec.get("project_title_en") or "Regression Analysis Report"),
        "items": items,
    }


def build_python_quality_checks() -> list[dict[str, Any]]:
    results_path = LOG_DIR / "model_results.csv"
    checks: list[dict[str, Any]] = []
    if not results_path.exists():
        return checks
    frame = pd.read_csv(results_path, encoding="utf-8-sig")
    if frame.empty:
        return checks
    for keys, group in frame.groupby(["analysis_line", "module_type", "module_name", "model_label"], dropna=False):
        analysis_line, module_type, module_name, model_label = keys
        nobs = pd.to_numeric(group["nobs"], errors="coerce").dropna()
        coef = pd.to_numeric(group["coef"], errors="coerce")
        r2 = pd.to_numeric(group["r2"], errors="coerce")
        if not nobs.empty and float(nobs.iloc[0]) <= 0:
            checks.append({"analysis_line": analysis_line, "module_type": module_type, "module_name": module_name, "model_label": model_label, "check_name": "zero_nobs", "message": "Python 复核发现有效样本量是 0。", "check_value": 0})
        if coef.isna().all():
            checks.append({"analysis_line": analysis_line, "module_type": module_type, "module_name": module_name, "model_label": model_label, "check_name": "missing_focus_term", "message": "Python 复核发现关注系数全是空的。", "check_value": None})
        if not r2.dropna().empty and any(abs(float(value)) > 1.0 for value in r2.dropna()):
            checks.append({"analysis_line": analysis_line, "module_type": module_type, "module_name": module_name, "model_label": model_label, "check_name": "abnormal_r2", "message": "Python 复核发现 R2 超出常见范围。", "check_value": float(r2.dropna().iloc[0])})
    return checks


def merge_quality_checks() -> None:
    quality_path = LOG_DIR / "quality_checks.csv"
    existing = pd.read_csv(quality_path, encoding="utf-8-sig") if quality_path.exists() else pd.DataFrame()
    python_checks = pd.DataFrame(build_python_quality_checks())
    if existing.empty and python_checks.empty:
        return
    if existing.empty:
        merged = python_checks
    elif python_checks.empty:
        merged = existing
    else:
        merged = pd.DataFrame([*existing.to_dict(orient="records"), *python_checks.to_dict(orient="records")])
    merged.to_csv(quality_path, index=False, encoding="utf-8-sig")


def write_empty_execution_outputs() -> None:
    pd.DataFrame(columns=["package", "installed", "install_attempted", "install_succeeded"]).to_csv(LOG_DIR / "package_status.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["analysis_line", "module_type", "module_name", "model_label", "estimator", "depvar", "focus_term", "ok", "nobs", "r2", "coef", "se", "pvalue", "pvalue_source", "error_code", "error_type", "error_message"]).to_csv(LOG_DIR / "model_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["analysis_line", "module_type", "module_name", "model_label", "check_name", "message", "check_value"]).to_csv(LOG_DIR / "quality_checks.csv", index=False, encoding="utf-8-sig")


def safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def build_quality_summary(spec: dict[str, Any]) -> dict[str, Any]:
    results_path = LOG_DIR / "model_results.csv"
    quality_path = LOG_DIR / "quality_checks.csv"
    package_path = LOG_DIR / "package_status.csv"
    results = pd.read_csv(results_path, encoding="utf-8-sig") if results_path.exists() else pd.DataFrame()
    quality = pd.read_csv(quality_path, encoding="utf-8-sig") if quality_path.exists() else pd.DataFrame()
    packages = pd.read_csv(package_path, encoding="utf-8-sig") if package_path.exists() else pd.DataFrame()
    summary: dict[str, Any] = {
        "project_title": spec.get("project_title"),
        "analysis_line_count": len(analysis_lines(spec)),
        "package_status": [dict((key, safe_value(value)) for key, value in row.items()) for row in packages.to_dict(orient="records")],
        "quality_checks": [dict((key, safe_value(value)) for key, value in row.items()) for row in quality.to_dict(orient="records")],
        "modules": [],
    }
    for line_spec in analysis_lines(spec):
        line_id = line_spec["line_id"]
        line_rows = results[results["analysis_line"] == line_id] if not results.empty else pd.DataFrame()
        line_quality = quality[quality["analysis_line"] == line_id] if not quality.empty else pd.DataFrame()
        summary["modules"].append({"line_id": line_id, "line_type": line_spec.get("line_type"), "result_row_count": int(len(line_rows)), "failed_model_count": int((line_rows["ok"] == 0).sum()) if not line_rows.empty else 0, "quality_issue_count": int(len(line_quality))})
    return summary


def write_formal_outputs(spec: dict[str, Any], summary_path: Path) -> None:
    summary_payload = build_quality_summary(spec)
    save_json(OUTPUT_RESULTS_SUMMARIES_DIR / "run_summary.json", summary_payload)
    save_json(
        OUTPUT_RESULTS_SUMMARIES_DIR / "baseline_summary.json",
        {
            "project_title": spec.get("project_title"),
            "analysis_line_count": summary_payload.get("analysis_line_count"),
            "modules": summary_payload.get("modules"),
        },
    )
    save_json(
        OUTPUT_RESULTS_FOLLOWUPS_DIR / "followup_candidates.json",
        {
            "project_title": spec.get("project_title"),
            "selection_mode": "followup_batch",
            "note": "基于 baseline 结果筛选后，再生成小批次 follow-up master do-file。",
            "modules": summary_payload.get("modules"),
        },
    )
    save_json(
        OUTPUT_RESULTS_DIR / "report_config.json",
        build_report_config(spec)
        if has_models(spec)
        else {"title": spec.get("project_title"), "title_en": str(spec.get("project_title") or "Regression Analysis Report"), "items": []},
    )
    save_json(OUTPUT_RESULTS_SUMMARIES_DIR / "summary_index.json", {"run_summary": str(summary_path), "baseline_summary": str(OUTPUT_RESULTS_SUMMARIES_DIR / "baseline_summary.json")})


def invoke_stata(stata_path: Path, do_path: Path) -> None:
    command = [str(stata_path), "/e", "do", str(do_path)]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=str(OUTPUT_RUNTIME_LOGS_DIR))
    auto_task_log = ROOT / f"{do_path.stem}.log"
    if auto_task_log.exists():
        shutil.move(str(auto_task_log), str(OUTPUT_RUNTIME_LOGS_DIR / auto_task_log.name))
    if result.returncode != 0:
        tail = "\n".join((result.stderr or result.stdout).strip().splitlines()[-30:])
        raise RuntimeError(f"Stata 执行失败。\n{tail}")


def main() -> None:
    ensure_skill_output_dirs()
    ensure_workspace_dirs()
    if sys.stdin is not None and sys.stdin.isatty():
        try:
            answer = input("提示 是否开始一个新课题？输入 y 会清空 output 里的当前配置和产出，但保留 data：").strip().lower()
        except EOFError:
            answer = ""
        if answer in {"y", "yes", "1", "是"}:
            reset_for_new_project()
            print("完成 已按新课题模式清空 output 里的旧配置和旧结果，data 保留不动。")
    for legacy in (ROOT / "tmp_install_probe.log", ROOT / "tmp_stata_skill_workflow.log", ROOT / "tmp_task.log", ROOT / "task.log"):
        if legacy.exists():
            shutil.move(str(legacy), str(OUTPUT_RUNTIME_LOGS_DIR / legacy.name))
    generated = write_default_workflow_artifacts()
    spec = json.loads(DEFAULT_SPEC_PATH.read_text(encoding="utf-8"))
    if has_models(spec):
        build_dynamic_do(spec, DEFAULT_DO_PATH)
        stata_path = find_stata_executable()
        invoke_stata(stata_path, DEFAULT_DO_PATH)
        render_module_tables()
        merge_quality_checks()
    else:
        DEFAULT_DO_PATH.write_text("* 当前任务还没选具体模型，所以先不执行 Stata。\n", encoding="utf-8")
        write_empty_execution_outputs()
    summary_path = LOG_DIR / "run_summary.json"
    save_json(summary_path, build_quality_summary(spec))
    write_formal_outputs(spec, summary_path)
    print(json.dumps({"spec": str(generated["spec"]), "diagnostics": str(generated["diagnostics"]), "template": str(generated["template"]), "do_file": str(DEFAULT_DO_PATH), "summary": str(summary_path), "figure_dir": str(FIGURE_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
