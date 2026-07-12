from __future__ import annotations

import argparse
from pathlib import Path

from writing_pipeline_lib import (
    bibliography_asset_path,
    extract_cited_keys,
    parse_bib_keys,
    read_build_manifest_compatible,
    read_case_manifest_compatible,
    load_query_manifests,
    resolve_languages,
    resolve_shared_ref_v2_path,
    shared_build_dir,
    shared_ref_v3_language_path,
    utc_now_iso,
    write_build_manifest_compatible,
    write_json,
)

LANGUAGE_BIB_NAMES = {
    "zh": "ref_zh.bib",
    "en": "ref_en.bib",
}


def render_bibliography(entries: dict[str, str], keys: list[str]) -> str:
    return "\n".join(entries[key].rstrip() for key in keys).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a shared ref_v3.bib from citations used across the bilingual literature review.")
    parser.add_argument("--case-root", required=True, help="Path to the target review case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_case_manifest_compatible(case_root)
    build_manifest = read_build_manifest_compatible(case_root, case_manifest)
    query_manifests = load_query_manifests(case_root, case_manifest)
    ref_v2_path = resolve_shared_ref_v2_path(case_root, case_manifest, query_manifests)
    cited_keys: list[str] = []
    seen: set[str] = set()
    generated_reviews = build_manifest.get("generated_reviews", {})

    for language in resolve_languages(case_manifest):
        generated_rel = generated_reviews.get(language)
        if not generated_rel:
            continue
        tex_path = case_root / generated_rel
        if not tex_path.exists():
            continue
        for key in extract_cited_keys(tex_path.read_text(encoding="utf-8")):
            if key not in seen:
                seen.add(key)
                cited_keys.append(key)

    output_dir = shared_build_dir(case_root)
    output_path = output_dir / "ref_v3.bib"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_entries = {}
    if ref_v2_path and ref_v2_path.exists():
        source_entries = parse_bib_keys(ref_v2_path.read_text(encoding="utf-8"))

    if not source_entries:
        output_path.write_text("% Shared ref_v2.bib is missing. Add bibliographic metadata before relying on ref_v3.bib.\n", encoding="utf-8")
    else:
        missing_from_ref_v2 = [key for key in cited_keys if key not in source_entries]
        if missing_from_ref_v2:
            missing = ", ".join(missing_from_ref_v2)
            raise KeyError(f"Cited keys are missing from shared ref_v2.bib: {missing}")

        approved_text = render_bibliography(source_entries, cited_keys)
        language_outputs: dict[str, str] = {}
        language_sources: dict[str, str] = {}
        languages = resolve_languages(case_manifest)
        bilingual_sources = {
            language: bibliography_asset_path(case_root, LANGUAGE_BIB_NAMES[language])
            for language in languages
            if language in LANGUAGE_BIB_NAMES
        }

        if len(bilingual_sources) == len(languages) and all(path.exists() for path in bilingual_sources.values()):
            for language in languages:
                source_path = bilingual_sources[language]
                entries = parse_bib_keys(source_path.read_text(encoding="utf-8"))
                missing_from_language = [key for key in cited_keys if key not in entries]
                if missing_from_language:
                    missing = ", ".join(missing_from_language)
                    raise KeyError(f"Cited keys are missing from {source_path.name}: {missing}")
                language_output_path = shared_ref_v3_language_path(case_root, language)
                rendered = render_bibliography(entries, cited_keys)
                language_output_path.write_text(rendered, encoding="utf-8")
                language_outputs[language] = str(language_output_path)
                language_sources[language] = str(source_path)

            zh_output_path = shared_ref_v3_language_path(case_root, "zh")
            output_path.write_text(zh_output_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            output_path.write_text(approved_text, encoding="utf-8")

    build_manifest["cited_keys"] = cited_keys
    build_manifest["shared_ref_v3_path"] = str(output_path.relative_to(case_root)).replace("\\", "/")
    build_manifest["last_materialized_at"] = build_manifest.get("last_materialized_at") or utc_now_iso()
    write_build_manifest_compatible(case_root, case_manifest, build_manifest)
    report_path = case_root / "outputs" / "runtime" / "build_ref_v3_report.json"
    write_json(
        report_path,
        {
            "case_root": str(case_root),
            "generated_reviews": generated_reviews,
            "shared_ref_v2_path": str(ref_v2_path) if ref_v2_path else None,
            "shared_ref_v3_path": str(output_path),
            "language_bibliography_sources": language_sources if source_entries else {},
            "language_shared_ref_v3_paths": language_outputs if source_entries else {},
            "cited_keys": cited_keys,
        },
    )

    print(f"Built shared ref_v3.bib for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
