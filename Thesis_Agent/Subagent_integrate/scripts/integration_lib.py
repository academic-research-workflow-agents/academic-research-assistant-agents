from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SUBAGENT_ROOT.parent
EXAMPLES_ROOT = SUBAGENT_ROOT / "examples"
BUSINESS_SUBAGENTS = [
    {"name": "Subagent_read_paper", "role": "reading_source"},
    {"name": "Subagent_process_data", "role": "data_asset_builder"},
    {"name": "Subagent_regress_stata", "role": "regression_session"},
    {"name": "Subagent_write_latex", "role": "writing_case"},
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relpath_from(base: Path, target: Path) -> str:
    return os.path.relpath(target, base).replace("\\", "/")


def resolve_existing_case_root() -> Path:
    env_case_root = os.environ.get("INTEGRATION_CASE_ROOT")
    if env_case_root:
        candidate = Path(env_case_root).resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"INTEGRATION_CASE_ROOT does not exist: {candidate}")

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if candidate.parent.parent == EXAMPLES_ROOT:
            return candidate

    raise RuntimeError(
        "Unable to resolve the active integration child_case. "
        "Set INTEGRATION_CASE_ROOT or run the command from examples/<thesis_case>/<child_case>."
    )


def manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "thesis_coordination_manifest.json"


def report_md_path(case_root: Path) -> Path:
    return case_root / "outputs" / "thesis_coordination_report.md"


def scan_json_path(case_root: Path) -> Path:
    return case_root / "outputs" / "thesis_coordination_scan.json"


def ensure_case_skeleton(case_root: Path) -> None:
    for directory in (
        case_root / "manifests",
        case_root / "requests",
        case_root / "outputs",
        case_root / "scripts",
    ):
        directory.mkdir(parents=True, exist_ok=True)


def default_case_agents(case_name: str) -> str:
    return f"""# {case_name}

## Role
这是 integration 层的通用 `child_case`。

它只负责：
- 维护 thesis-wide coordination manifest
- 记录 linked cases、readiness gates、blockers 和 next action
- 在不改动其他业务 case 的前提下给出顺序统筹建议

它不负责：
- 代做 reading、数据处理、回归或写作
- 替其他 subagent 自动新建真实工作 case
- 替代 root 或主 thesis-wide integration case

## Documentation Rule
- `AGENTS.md` 面向 AI，只写合同、边界、工程规则和隐私规则。
- `README.md` 面向用户，只写何时进入、要准备什么、如何开始。
- 嵌套子目录不要再放 `README.md`；过程说明使用语义化文件名。

## Storage Rule
- 本 case 是唯一允许承载当前 integration 运行内容的单元。
- `manifests/` 保存 coordination manifest 或 package registry。
- `requests/` 保存用户提供的输入、范围决策或说明副本。
- `outputs/` 根层只保留当前 live surface；历史快照进入 `outputs/archive/`。
- `scripts/` 只保存本 case 专用脚本。

## Independence Rule
- manifests、scripts、registries 只允许引用本 workspace 内部路径。
- 不使用文件系统链接、外部挂载或相对路径跳回历史系统。
- 不在上层文档公开私有 case 状态。
- 所有临时产物必须放在本 child_case 内部。
"""


def default_case_readme(case_name: str) -> str:
    return f"""# {case_name}

这是一个 integration `child_case`。

## 这是干什么的
- 记录当前 `thesis_case` 在四个业务 subagent 下的 child-case 映射
- 提示下一步应该先进入哪个 subagent
- 在阶段切换前暴露 blockers 和 readiness gates

## 如何继续
1. 先确认当前 `thesis_case`。
2. 运行 `refresh_coordination_manifest.py` 刷新 linked cases。
3. 根据 `outputs/thesis_coordination_report.md` 里的 next action 决定下一步进入哪个 subagent。

## 入口文件
- `manifests/thesis_coordination_manifest.json`
- `outputs/thesis_coordination_report.md`
"""


def default_placeholder_links(case_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in BUSINESS_SUBAGENTS:
        target = (
            WORKSPACE_ROOT
            / item["name"]
            / "examples"
            / "_empty_thesis_case"
            / "_empty_child_case"
        ).resolve()
        entries.append(
            {
                "subagent": item["name"],
                "child_case": "_empty_child_case",
                "relative_path": relpath_from(case_root, target),
                "role": item["role"],
                "status": "placeholder",
            }
        )
    return entries


def default_coordination_manifest(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "thesis_case": case_root.parent.name,
        "active_mode": "integration",
        "linked_cases": default_placeholder_links(case_root),
        "readiness_gates": {
            "reading_ready": False,
            "process_ready": False,
            "regression_ready": False,
            "empirical_ready": False,
            "writing_ready": False,
        },
        "blockers": [
            "No real business child_case has been registered yet.",
            "Confirm the thesis_case, then create or identify child_cases under the four business subagents.",
        ],
        "next_action": "Start by confirming or creating a reading child_case under Subagent_read_paper.",
        "updated_at": utc_now_iso(),
    }


def scan_business_cases(case_root: Path, thesis_case: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    thesis_name = thesis_case or case_root.parent.name
    linked_cases: list[dict[str, Any]] = []
    blockers: list[str] = []
    for item in BUSINESS_SUBAGENTS:
        thesis_root = WORKSPACE_ROOT / item["name"] / "examples" / thesis_name
        if not thesis_root.exists():
            blockers.append(f"Missing thesis namespace under {item['name']}/examples/{thesis_name}.")
            continue
        children = sorted(path for path in thesis_root.iterdir() if path.is_dir())
        if not children:
            blockers.append(f"No child_case found under {item['name']}/examples/{thesis_name}.")
            continue
        for child in children:
            linked_cases.append(
                {
                    "subagent": item["name"],
                    "child_case": child.name,
                    "relative_path": relpath_from(case_root, child.resolve()),
                    "role": item["role"],
                    "status": "present",
                }
            )
    return linked_cases, blockers


def derive_readiness(linked_cases: list[dict[str, Any]]) -> dict[str, bool]:
    reading_ready = any(item["subagent"] == "Subagent_read_paper" and not item["child_case"].startswith("_") for item in linked_cases)
    process_ready = any(item["subagent"] == "Subagent_process_data" and not item["child_case"].startswith("_") for item in linked_cases)
    regression_ready = any(item["subagent"] == "Subagent_regress_stata" and not item["child_case"].startswith("_") for item in linked_cases)
    writing_ready = any(item["subagent"] == "Subagent_write_latex" and not item["child_case"].startswith("_") for item in linked_cases)
    return {
        "reading_ready": reading_ready,
        "process_ready": process_ready,
        "regression_ready": regression_ready,
        "empirical_ready": process_ready or regression_ready,
        "writing_ready": writing_ready,
    }


def determine_active_mode(readiness_gates: dict[str, bool]) -> str:
    if not readiness_gates["reading_ready"]:
        return "reading"
    if not readiness_gates["empirical_ready"]:
        return "empirical_asset_building"
    if not readiness_gates["writing_ready"]:
        return "thesis_writing"
    return "integration"


def determine_next_action(thesis_case: str, readiness_gates: dict[str, bool]) -> str:
    if not readiness_gates["reading_ready"]:
        return f"Create or confirm a reading child_case under Subagent_read_paper/examples/{thesis_case}/, then refresh this manifest."
    if not readiness_gates["process_ready"]:
        return f"Create or confirm a data-process child_case under Subagent_process_data/examples/{thesis_case}/."
    if not readiness_gates["regression_ready"]:
        return f"Create or confirm a regression child_case under Subagent_regress_stata/examples/{thesis_case}/ when the empirical asset is regression-ready."
    if not readiness_gates["writing_ready"]:
        return f"Create or confirm a writing child_case under Subagent_write_latex/examples/{thesis_case}/."
    return "All four business layers are mapped. Use this integration case to route the next concrete execution step by user intent."


def build_coordination_manifest(case_root: Path) -> dict[str, Any]:
    linked_cases, blockers = scan_business_cases(case_root)
    readiness_gates = derive_readiness(linked_cases)
    return {
        "schema_version": 1,
        "thesis_case": case_root.parent.name,
        "active_mode": determine_active_mode(readiness_gates),
        "linked_cases": linked_cases,
        "readiness_gates": readiness_gates,
        "blockers": blockers,
        "next_action": determine_next_action(case_root.parent.name, readiness_gates),
        "updated_at": utc_now_iso(),
    }


def build_scan_payload(case_root: Path) -> dict[str, Any]:
    linked_cases, blockers = scan_business_cases(case_root)
    return {
        "schema_version": 1,
        "thesis_case": case_root.parent.name,
        "linked_cases": linked_cases,
        "blockers": blockers,
        "scanned_at": utc_now_iso(),
    }


def build_coordination_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Thesis Coordination Report",
        "",
        f"- `thesis_case`: `{manifest['thesis_case']}`",
        f"- `active_mode`: `{manifest['active_mode']}`",
        f"- `updated_at`: `{manifest.get('updated_at', '')}`",
        "",
        "## Linked Cases",
        "",
    ]
    linked_cases = list(manifest.get("linked_cases") or [])
    if linked_cases:
        for item in linked_cases:
            lines.append(
                f"- `{item['subagent']}` / `{item['child_case']}` / `{item['status']}` / `{item['relative_path']}`"
            )
    else:
        lines.append("- No linked business case found yet.")
    lines.extend(["", "## Readiness Gates", ""])
    for key, value in dict(manifest.get("readiness_gates") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Blockers", ""])
    blockers = list(manifest.get("blockers") or [])
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- No blocker detected at the coordination layer.")
    lines.extend(["", "## Next Action", "", f"- {manifest.get('next_action', '')}", ""])
    return "\n".join(lines)
