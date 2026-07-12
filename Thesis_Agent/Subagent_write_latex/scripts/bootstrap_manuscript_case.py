from __future__ import annotations

import argparse
from pathlib import Path

from sync_case_skills import sync_case_skills_for_case
from writing_pipeline_lib import (
    asset_manifest_path,
    case_manifest_path,
    chapter_blueprint,
    chapter_manifest_path,
    chapter_placeholder,
    default_asset_manifest,
    default_build_manifest,
    default_case_agents,
    default_case_manifest,
    default_case_readme,
    default_chapter_manifest,
    ensure_case_skeleton,
    ensure_text,
    normalize_authoring_mode,
    write_json,
    build_manifest_path,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap a writing-layer manuscript case and seed case-local personal skills."
    )
    parser.add_argument("--case-root", required=True, help="Path to the target writing case root.")
    parser.add_argument(
        "--authoring-mode",
        default="markdown",
        help="Authoring mode: markdown or direct_latex.",
    )
    parser.add_argument(
        "--overwrite-placeholders",
        action="store_true",
        help="Overwrite existing placeholder files.",
    )
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    mode = normalize_authoring_mode(args.authoring_mode)

    ensure_case_skeleton(case_root, mode)
    ensure_text(case_root / "AGENTS.md", default_case_agents(case_root.name), overwrite=False)
    ensure_text(case_root / "README.md", default_case_readme(case_root.name, mode), overwrite=False)

    write_json(case_manifest_path(case_root), default_case_manifest(case_root, mode))
    write_json(asset_manifest_path(case_root), default_asset_manifest())
    write_json(chapter_manifest_path(case_root), default_chapter_manifest(mode))
    write_json(build_manifest_path(case_root), default_build_manifest(case_root, mode))
    skill_sync_report = sync_case_skills_for_case(case_root, force_refresh=False)

    for chapter in chapter_blueprint(mode):
        for language in ("zh", "en"):
            source_rel = chapter.get(f"{language}_source")
            if not source_rel:
                continue
            source_path = case_root / source_rel
            ensure_text(
                source_path,
                chapter_placeholder(chapter["id"], chapter["kind"], language, mode),
                overwrite=args.overwrite_placeholders,
            )

    print(f"Bootstrapped writing case: {case_root}")
    print(f"Authoring mode: {mode}")
    print(f"Seeded personal skills: {len(skill_sync_report['skills'])}")
    print(f"Skill sync report: {skill_sync_report['report_path']}")


if __name__ == "__main__":
    main()
