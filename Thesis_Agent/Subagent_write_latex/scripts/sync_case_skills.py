from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

from writing_pipeline_lib import utc_now_iso, write_json


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
RAW_SKILLS_ROOT = SUBAGENT_ROOT / "skills"
OVERLAY_HEADING_EN = "## Personal Overlay"
OVERLAY_HEADING_ZH = "## 私人化覆盖规则"

PERSONAL_OVERLAY_EN = f"""
{OVERLAY_HEADING_EN}

- Read `references/style-profile.md` when the task should match this case's writing habits more closely.
- Treat the latest user-revised draft as the highest-priority anchor, and default to patching rather than broad rewriting.
- Keep the raw skill's hard rules unless this case's style profile narrows them further.
""".strip()

PERSONAL_OVERLAY_ZH = f"""
{OVERLAY_HEADING_ZH}

- 当任务需要更贴近当前 case 的写作习惯时，优先读取 `references/style-profile.md`。
- 最新的用户手改稿是最高优先级锚点，后续默认做 patch，不做大段重写。
- 除非当前 case 的风格画像进一步收窄，否则继续遵守 raw skill 的硬规则。
""".strip()


def raw_skill_dirs(root: Path = RAW_SKILLS_ROOT) -> list[Path]:
    return sorted(
        [
            path
            for path in root.iterdir()
            if path.is_dir() and (path / "SKILL.md").exists()
        ],
        key=lambda item: item.name.lower(),
    )


def personal_skill_name(raw_skill_name: str) -> str:
    return f"{raw_skill_name}-personal"


def infer_skill_language(skill_name: str) -> str:
    if skill_name.endswith("-zh"):
        return "zh"
    if skill_name.endswith("-en"):
        return "en"
    return "generic"


def rewrite_frontmatter_name(skill_text: str, personal_name: str) -> str:
    return re.sub(r"(?m)^name:\s*([^\n]+)$", f"name: {personal_name}", skill_text, count=1)


def append_personal_overlay(skill_text: str, language: str) -> str:
    overlay = PERSONAL_OVERLAY_ZH if language == "zh" else PERSONAL_OVERLAY_EN
    if OVERLAY_HEADING_ZH in skill_text or OVERLAY_HEADING_EN in skill_text:
        return skill_text
    normalized = skill_text.rstrip() + "\n\n" + overlay + "\n"
    return normalized


def style_profile_template(language: str, case_name: str, skill_name: str) -> str:
    if language == "zh":
        return f"""# 私人风格画像（中文）

这是 `{case_name}` 的 case-local 私人风格画像，占位模板对应技能 `{skill_name}`。

## 怎么用

- 记录当前 case 已确认的中文写作习惯
- 只描述结构、节奏、变量解释和结果推进方式
- 不照搬学校格式、不照搬原句

## 可以逐步补充的内容

- 这一篇最稳定的章节推进顺序
- 变量说明和模型设定常用的展开方式
- 回归结果、稳健性、机制分析的叙述节奏
- 用户明确保留或明确反感的表达习惯

## 硬规则

- 最新用户手改稿优先于任何旧 assistant 版本
- 没确认的风格不要写成刚性规则
- 风格画像只服务当前 case，不回写 subagent 级 raw skill
"""

    return f"""# Personal Style Profile (English)

This is the case-local personal style profile for `{case_name}` and skill `{skill_name}`.

## What To Store Here

- stable section-level habits for this case
- preferred structure for variables, methods, and results discussion
- result-interpretation rhythm that the user has actually accepted
- phrases or moves to avoid in this case

## Hard Rules

- the latest user-revised draft outranks any older assistant rewrite
- do not turn tentative preferences into rigid rules too early
- this profile is case-local only and must not overwrite the subagent raw skill
"""


def copy_missing_tree(source_root: Path, target_root: Path) -> list[str]:
    copied: list[str] = []
    for source_path in source_root.rglob("*"):
        relative = source_path.relative_to(source_root)
        target_path = target_root / relative
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        if relative.as_posix() == "SKILL.md":
            continue
        if target_path.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied.append(relative.as_posix())
    return copied


def sync_one_skill(raw_skill_dir: Path, case_skill_root: Path, force_refresh: bool, case_name: str) -> dict[str, Any]:
    raw_skill_name = raw_skill_dir.name
    language = infer_skill_language(raw_skill_name)
    personal_name = personal_skill_name(raw_skill_name)
    target_dir = case_skill_root / personal_name
    report: dict[str, Any] = {
        "raw_skill_name": raw_skill_name,
        "personal_skill_name": personal_name,
        "raw_skill_dir": str(raw_skill_dir),
        "target_dir": str(target_dir),
        "language": language,
        "mode": "force_refresh" if force_refresh else "refresh_missing_only",
        "directory_action": "preserved",
        "copied_files": [],
        "skill_md_action": "preserved",
        "style_profile_action": "preserved",
    }

    if force_refresh and target_dir.exists():
        shutil.rmtree(target_dir)
    if not target_dir.exists():
        shutil.copytree(raw_skill_dir, target_dir)
        report["directory_action"] = "created"
    else:
        report["copied_files"] = copy_missing_tree(raw_skill_dir, target_dir)
        if report["copied_files"]:
            report["directory_action"] = "updated_missing_files"

    raw_skill_md = (raw_skill_dir / "SKILL.md").read_text(encoding="utf-8")
    personal_skill_md = append_personal_overlay(
        rewrite_frontmatter_name(raw_skill_md, personal_name),
        language,
    )
    skill_md_path = target_dir / "SKILL.md"
    if force_refresh or report["directory_action"] == "created" or not skill_md_path.exists():
        skill_md_path.write_text(personal_skill_md, encoding="utf-8")
        report["skill_md_action"] = "written"

    style_profile_path = target_dir / "references" / "style-profile.md"
    if force_refresh or not style_profile_path.exists():
        style_profile_path.parent.mkdir(parents=True, exist_ok=True)
        style_profile_path.write_text(style_profile_template(language, case_name, personal_name), encoding="utf-8")
        report["style_profile_action"] = "written"

    return report


def sync_case_skills_for_case(case_root: Path, force_refresh: bool = False) -> dict[str, Any]:
    case_root = case_root.resolve()
    case_skill_root = case_root / "skills"
    case_skill_root.mkdir(parents=True, exist_ok=True)

    report = {
        "case_root": str(case_root),
        "case_name": case_root.name,
        "mode": "force_refresh" if force_refresh else "refresh_missing_only",
        "raw_skills_root": str(RAW_SKILLS_ROOT),
        "synced_at": utc_now_iso(),
        "skills": [],
    }

    for raw_skill_dir in raw_skill_dirs():
        report["skills"].append(sync_one_skill(raw_skill_dir, case_skill_root, force_refresh, case_root.name))

    report_path = case_root / "outputs" / "runtime" / "sync_case_skills_report.json"
    write_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed or refresh case-local personal skills from subagent raw skills."
    )
    parser.add_argument("--case-root", required=True, help="Path to the writing case root.")
    parser.add_argument(
        "--refresh-missing-only",
        action="store_true",
        help="Refresh only missing skill files. This is also the default behavior.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Recreate personal skills from raw skills and overwrite case-local generated copies.",
    )
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    if args.force_refresh and args.refresh_missing_only:
        raise ValueError("Choose at most one refresh mode.")

    report = sync_case_skills_for_case(case_root, force_refresh=args.force_refresh)
    print(f"Synced personal skills for: {case_root}")
    print(f"Mode: {report['mode']}")
    print(f"Report: {report['report_path']}")


if __name__ == "__main__":
    main()
