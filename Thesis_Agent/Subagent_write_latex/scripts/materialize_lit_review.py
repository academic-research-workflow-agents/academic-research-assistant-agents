from __future__ import annotations

import argparse
from pathlib import Path

from writing_pipeline_lib import (
    MarkdownRenderError,
    ReviewBoundaryError,
    generated_review_path,
    read_build_manifest_compatible,
    read_case_manifest_compatible,
    read_chapter_manifest_compatible,
    render_markdown_document,
    resolve_languages,
    runtime_dir,
    chapter_source_path,
    ensure_review_identity,
    utc_now_iso,
    write_build_manifest_compatible,
    write_json,
)


def materialize_one_language(case_root: Path, case_manifest: dict, chapter_manifest: dict, language: str) -> dict:
    mode = case_manifest["authoring_mode"]
    source_path = chapter_source_path(case_root, chapter_manifest, language)
    if not source_path.exists():
        raise FileNotFoundError(f"Review source does not exist: {source_path}")

    raw_text = source_path.read_text(encoding="utf-8")
    review_identity = ensure_review_identity(raw_text, language)
    report_entry: dict[str, object] = {
        "language": language,
        "source_path": str(source_path),
        "authoring_mode": mode,
        "status": "pending",
        "review_identity_validation": review_identity,
    }

    if mode == "markdown":
        title_fallback = "文献综述" if language == "zh" else "Literature Review"
        render_result = render_markdown_document(raw_text, title_fallback, case_manifest.get("markdown_renderer"))
        rendered = render_result["rendered"]
        report_entry["renderer"] = "pandoc"
        report_entry["pandoc_command"] = render_result["pandoc_command"]
        report_entry["warnings"] = render_result["warnings"]
        report_entry["heading_validation"] = render_result["heading_validation"]
    else:
        rendered = raw_text.strip() + "\n"
        report_entry["renderer"] = "direct_latex"
        report_entry["warnings"] = []
        report_entry["heading_validation"] = {
            "checked": False,
            "rule": "direct_latex_mode",
            "valid": True,
            "violations": [],
        }

    output_path = generated_review_path(case_root, language)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    report_entry["output_path"] = str(output_path)
    report_entry["status"] = "generated"
    return report_entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize bilingual literature-review sources into generated LaTeX chapters.")
    parser.add_argument("--case-root", required=True, help="Path to the target review case root.")
    parser.add_argument("--language", default=None, help="Optional language override: zh or en.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_case_manifest_compatible(case_root)
    chapter_manifest = read_chapter_manifest_compatible(case_root, case_manifest)
    build_manifest = read_build_manifest_compatible(case_root, case_manifest)
    languages = resolve_languages(case_manifest, args.language)
    report = {
        "case_root": str(case_root),
        "authoring_mode": case_manifest["authoring_mode"],
        "generated_files": [],
        "errors": [],
    }

    for language in languages:
        try:
            entry = materialize_one_language(case_root, case_manifest, chapter_manifest, language)
            report["generated_files"].append(entry)
            build_manifest.setdefault("generated_reviews", {})[language] = str(generated_review_path(case_root, language).relative_to(case_root)).replace("\\", "/")
        except (FileNotFoundError, MarkdownRenderError, ReviewBoundaryError) as exc:
            error_entry = {
                "language": language,
                "status": "failed",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
            }
            if isinstance(exc, MarkdownRenderError):
                error_entry["error_details"] = exc.details
            if isinstance(exc, ReviewBoundaryError):
                error_entry["violations"] = exc.violations
            report["errors"].append(error_entry)

    build_manifest["last_materialized_at"] = utc_now_iso()
    build_manifest["status"] = "materialized" if not report["errors"] else "materialize_failed"
    write_build_manifest_compatible(case_root, case_manifest, build_manifest)
    report_path = runtime_dir(case_root) / "materialize_lit_review_report.json"
    write_json(report_path, report)
    if report["errors"]:
        first = report["errors"][0]
        raise RuntimeError(
            f"Materialize literature review failed for {len(report['errors'])} language(s). "
            f"First failure: {first['language']} {first['error_type']} - {first['error_message']}"
        )

    print(f"Materialized literature review for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
