from __future__ import annotations

import argparse
from pathlib import Path

from writing_pipeline_lib import (
    MarkdownRenderError,
    build_manifest_path,
    case_manifest_path,
    chapter_manifest_path,
    generated_chapter_dir,
    normalize_authoring_mode,
    read_json,
    render_markdown_document,
    resolve_case_path,
    utc_now_iso,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize bilingual manuscript sources into chapter .tex files.")
    parser.add_argument("--case-root", required=True, help="Path to the writing case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_json(case_manifest_path(case_root), {})
    chapter_manifest = read_json(chapter_manifest_path(case_root), {})
    build_manifest = read_json(build_manifest_path(case_root), {})

    mode = normalize_authoring_mode(case_manifest.get("authoring_mode") or chapter_manifest.get("authoring_mode"))
    output_root = generated_chapter_dir(case_root)
    output_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "case_root": str(case_root),
        "authoring_mode": mode,
        "generated_files": [],
        "errors": [],
    }
    markdown_renderer = case_manifest.get("markdown_renderer")
    failures: list[dict[str, object]] = []

    for chapter in chapter_manifest.get("chapters", []):
        kind = chapter["kind"]
        for language in ("zh", "en"):
            source_rel = chapter.get(f"{language}_source")
            target_rel = chapter.get(f"{language}_target")
            if not source_rel or not target_rel:
                continue

            source_path = resolve_case_path(case_root, source_rel)
            if source_path is None or not source_path.exists():
                continue

            target_path = output_root / language / Path(target_rel).name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                target_path.unlink()
            raw_text = source_path.read_text(encoding="utf-8")
            report_entry: dict[str, object] = {
                "chapter_id": chapter["id"],
                "language": language,
                "kind": kind,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "status": "pending",
            }

            try:
                if mode == "markdown":
                    render_result = render_markdown_document(raw_text, language, kind, markdown_renderer)
                    rendered = str(render_result["rendered"])
                    report_entry["renderer"] = render_result["renderer"]
                    report_entry["pandoc_command"] = render_result["pandoc_command"]
                    report_entry["heading_validation"] = render_result["heading_validation"]
                    report_entry["raw_conversion_warnings"] = render_result["warnings"]
                else:
                    rendered = raw_text.strip() + "\n"
                    report_entry["renderer"] = {"engine": "direct_latex"}
                    report_entry["heading_validation"] = {
                        "checked": False,
                        "rule": "direct_latex_mode",
                        "valid": True,
                        "violations": [],
                    }
                    report_entry["raw_conversion_warnings"] = []
            except MarkdownRenderError as exc:
                report_entry["status"] = "failed"
                report_entry["error_type"] = exc.category
                report_entry["error_message"] = str(exc)
                if exc.details:
                    report_entry["error_details"] = exc.details
                report["generated_files"].append(report_entry)
                failures.append(report_entry)
                continue

            target_path.write_text(rendered, encoding="utf-8")
            report_entry["status"] = "generated"
            report["generated_files"].append(report_entry)

    build_manifest["authoring_mode"] = mode
    build_manifest["generated_chapter_dir"] = "outputs/build/generated_chapters"
    build_manifest["last_materialized_at"] = utc_now_iso()
    report_path = case_root / "outputs" / "runtime" / "materialize_chapters_report.json"
    report["errors"] = failures
    build_manifest["status"] = "materialized" if not failures else "materialize_failed"
    write_json(build_manifest_path(case_root), build_manifest)
    write_json(report_path, report)
    if failures:
        first_failure = failures[0]
        raise RuntimeError(
            "Materialize chapters failed for "
            f"{len(failures)} file(s). First failure: "
            f"{first_failure['chapter_id']}[{first_failure['language']}] {first_failure['error_type']} - {first_failure['error_message']}"
        )
    print(f"Materialized chapters for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
