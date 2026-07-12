from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from writing_pipeline_lib import (
    chapter_manifest_path,
    chapter_source_path,
    load_query_manifests,
    outline_manifest_path,
    outline_scaffold,
    read_case_manifest_compatible,
    read_chapter_manifest_compatible,
    read_outline_manifest_compatible,
    write_json,
)


def build_sections(language: str, query_manifests: list[dict[str, Any]], allowed_keys: list[str]) -> list[dict[str, Any]]:
    intro_title = "综述范围与组织逻辑" if language == "zh" else "Scope And Organizing Logic"
    intro_purpose = (
        "界定本综述的主题边界、比较维度与文献组织方式。"
        if language == "zh"
        else "Define the thematic scope, comparison axes, and organizing logic of the review."
    )
    sections: list[dict[str, Any]] = [
        {
            "section_id": "scope",
            "section_title": intro_title,
            "purpose": intro_purpose,
            "claims_to_cover": [],
            "planned_citations": allowed_keys[:5],
            "status": "draft",
        }
    ]

    for query_manifest in query_manifests:
        info_item = query_manifest.get("info_item") or query_manifest.get("query_id") or "topic"
        sections.append(
            {
                "section_id": f"strand-{query_manifest.get('query_id', info_item)}",
                "section_title": (
                    f"围绕{info_item}的研究脉络与分歧"
                    if language == "zh"
                    else f"Research Strands And Disagreements On {info_item}"
                ),
                "purpose": (
                    f"比较现有文献中围绕{info_item}的主要发现、机制解释与争议点。"
                    if language == "zh"
                    else f"Compare the main findings, mechanism stories, and disagreements in the literature on {info_item}."
                ),
                "claims_to_cover": [
                    (
                        f"梳理{info_item}相关文献的主要比较维度。"
                        if language == "zh"
                        else f"Map the main comparison axes in the literature on {info_item}."
                    )
                ],
                "planned_citations": query_manifest.get("selected_citation_keys", [])[:12],
                "status": "draft",
            }
        )

    sections.append(
        {
            "section_id": "synthesis",
            "section_title": "综合评述与研究空白" if language == "zh" else "Synthesis And Research Gaps",
            "purpose": (
                "综合比较现有文献，保留分歧与未解决问题，而不是转入本文贡献或政策启示。"
                if language == "zh"
                else "Synthesize the literature while preserving disagreement and unresolved questions, without drifting into contribution claims or policy implications."
            ),
            "claims_to_cover": [],
            "planned_citations": allowed_keys[:8],
            "status": "draft",
        }
    )
    return sections


def maybe_refresh_placeholders(case_root: Path, case_manifest: dict[str, Any], chapter_manifest: dict[str, Any], sections: list[dict[str, Any]]) -> None:
    placeholders = {
        "\\chapter{文献综述}\n\n\\section{综述范围与组织逻辑}\n\n待补写。\n",
        "\\chapter{Literature Review}\n\n\\section{Scope And Organizing Logic}\n\nDraft content goes here.\n",
        "# 文献综述\n\n## 综述范围与组织逻辑\n\n待补写。\n",
        "# Literature Review\n\n## Scope And Organizing Logic\n\nDraft content goes here.\n",
    }
    mode = case_manifest["authoring_mode"]
    for language in ("zh", "en"):
        source_path = chapter_source_path(case_root, chapter_manifest, language)
        if not source_path.exists():
            continue
        current = source_path.read_text(encoding="utf-8")
        if current not in placeholders:
            continue
        source_path.write_text(outline_scaffold(sections, language, mode), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a literature-review outline from reading-layer query outputs.")
    parser.add_argument("--case-root", required=True, help="Path to the target review case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_case_manifest_compatible(case_root)
    chapter_manifest = read_chapter_manifest_compatible(case_root, case_manifest)
    outline_manifest = read_outline_manifest_compatible(case_root)
    language = case_manifest.get("default_language", "zh")
    query_manifests = load_query_manifests(case_root, case_manifest)
    sections = build_sections(language, query_manifests, list(case_manifest.get("allowed_citation_keys") or []))

    outline_manifest["case_id"] = case_manifest["case_id"]
    outline_manifest["sections"] = sections
    outline_manifest["approval_status"] = outline_manifest.get("approval_status", "pending")
    write_json(outline_manifest_path(case_root), outline_manifest)
    maybe_refresh_placeholders(case_root, case_manifest, chapter_manifest, sections)

    print(f"Outline manifest updated for: {case_root}")
    print(f"Chapter manifest: {chapter_manifest_path(case_root)}")


if __name__ == "__main__":
    main()
