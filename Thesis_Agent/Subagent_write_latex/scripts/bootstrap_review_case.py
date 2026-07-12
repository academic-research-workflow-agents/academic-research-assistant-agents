from __future__ import annotations

import argparse
from pathlib import Path

from sync_case_skills import sync_case_skills_for_case
from writing_pipeline_lib import (
    build_manifest_path,
    case_manifest_path,
    chapter_manifest_path,
    default_build_manifest,
    default_case_agents,
    default_case_manifest,
    default_case_readme,
    default_chapter_manifest,
    default_outline_manifest,
    default_requests_readme,
    ensure_case_skeleton,
    ensure_text,
    lit_review_placeholder,
    normalize_authoring_mode,
    outline_manifest_path,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a bilingual literature-review writing case.")
    parser.add_argument("--case-root", required=True, help="Path to the target writing case root.")
    parser.add_argument(
        "--authoring-mode",
        default="direct_latex",
        help="Authoring mode: direct_latex or markdown. New cases default to direct_latex.",
    )
    parser.add_argument(
        "--overwrite-placeholders",
        action="store_true",
        help="Overwrite existing placeholder manuscript files.",
    )
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    mode = normalize_authoring_mode(args.authoring_mode)

    ensure_case_skeleton(case_root)
    write_json(case_manifest_path(case_root), default_case_manifest(case_root, mode))
    write_json(outline_manifest_path(case_root), default_outline_manifest(case_root))
    write_json(chapter_manifest_path(case_root), default_chapter_manifest(mode))
    write_json(build_manifest_path(case_root), default_build_manifest(case_root, mode))

    ensure_text(case_root / "AGENTS.md", default_case_agents(case_root.name), overwrite=False)
    ensure_text(case_root / "README.md", default_case_readme(case_root.name, mode), overwrite=False)
    ensure_text(case_root / "requests" / "README.md", default_requests_readme(), overwrite=False)
    ensure_text(case_root / "manuscript" / "support" / "ref_v2.bib", "% Add the approved shared ref_v2 bibliography here.\n", overwrite=False)
    for language in ("zh", "en"):
        extension = ".md" if mode == "markdown" else ".tex"
        ensure_text(
            case_root / "manuscript" / language / f"lit_review{extension}",
            lit_review_placeholder(language, mode),
            overwrite=args.overwrite_placeholders,
        )

    sync_report = sync_case_skills_for_case(case_root, force_refresh=False)
    print(f"Bootstrapped writing case: {case_root}")
    print(f"Authoring mode: {mode}")
    print(f"Skill sync report: {sync_report['report_path']}")


if __name__ == "__main__":
    main()
