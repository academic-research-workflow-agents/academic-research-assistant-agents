from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from reading_pipeline_lib import (
    case_manifest_path,
    extract_pdf_attachments,
    load_bib_entries,
    make_manual_citation_key,
    normalize_attachment_path,
    paper_manifest_local_path,
    paper_manifest_path,
    read_json,
    resolve_case_path,
    utc_now_iso,
    write_json,
)


def build_linked_bib_entries(ref_bib_path: Path, existing_status: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    for entry in load_bib_entries(ref_bib_path):
        citation_key = entry["citation_key"]
        fields = entry["fields"]
        raw_file_field = fields.get("file")
        pdf_candidates = [Path(normalize_attachment_path(item)) for item in extract_pdf_attachments(raw_file_field)]
        resolved_pdf = next((candidate for candidate in pdf_candidates if candidate.exists()), None)
        previous = existing_status.get(citation_key, {})
        public_rows.append(
            {
                "citation_key": citation_key,
                "title": fields.get("title") or citation_key,
                "ingest_source": "linked_bib",
                "attachment_status": "resolved" if resolved_pdf else "unresolved",
                "selected_attachment_kind": "pdf" if resolved_pdf else None,
                "card_status": previous.get("card_status", "not_started"),
                "selection_stage": previous.get("selection_stage", "v1"),
            }
        )
        local_rows.append(
            {
                "citation_key": citation_key,
                "raw_file_field": raw_file_field,
                "resolved_pdf_path": str(resolved_pdf) if resolved_pdf else None,
                "linked_attachment_path": str(resolved_pdf) if resolved_pdf else None,
                "attachment_candidates": [str(candidate) for candidate in pdf_candidates],
            }
        )
    return public_rows, local_rows


def build_manual_pdf_entries(case_root: Path, existing_status: dict[str, dict[str, Any]], existing_local_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    input_root = case_root / "inputs" / "papers"
    public_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    known_paths = {item.get("resolved_pdf_path") for item in existing_local_rows if item.get("resolved_pdf_path")}
    existing_keys = set(existing_status)

    for pdf_path in sorted(input_root.rglob("*.pdf")):
        resolved = str(pdf_path.resolve())
        if resolved in known_paths:
            continue
        citation_key = make_manual_citation_key(pdf_path.stem, existing_keys)
        existing_keys.add(citation_key)
        public_rows.append(
            {
                "citation_key": citation_key,
                "title": pdf_path.stem,
                "ingest_source": "manual_pdf",
                "attachment_status": "resolved",
                "selected_attachment_kind": "pdf",
                "card_status": existing_status.get(citation_key, {}).get("card_status", "not_started"),
                "selection_stage": existing_status.get(citation_key, {}).get("selection_stage", "v1"),
            }
        )
        local_rows.append(
            {
                "citation_key": citation_key,
                "raw_file_field": None,
                "resolved_pdf_path": resolved,
                "linked_attachment_path": None,
                "attachment_candidates": [resolved],
            }
        )
    return public_rows, local_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or refresh paper manifests for a reading case.")
    parser.add_argument("--case-root", required=True, help="Path to the target reading case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_json(case_manifest_path(case_root), {})
    public_manifest = read_json(paper_manifest_path(case_root), {"papers": []})
    local_manifest = read_json(paper_manifest_local_path(case_root), {"papers": []})

    ingest_mode = case_manifest.get("ingest_mode", "manual_pdf")
    existing_status = {item["citation_key"]: item for item in public_manifest.get("papers", [])}

    public_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    runtime_report: dict[str, Any] = {
        "case_root": str(case_root),
        "ingest_mode": ingest_mode,
        "linked_bib": None,
        "manual_pdf_scan_count": 0,
        "updated_at": utc_now_iso(),
    }

    ref_bib = resolve_case_path(case_root, case_manifest.get("ref_bib_path"))
    if ingest_mode in {"linked_bib", "mixed"} and ref_bib and ref_bib.exists():
        bib_public_rows, bib_local_rows = build_linked_bib_entries(ref_bib, existing_status)
        public_rows.extend(bib_public_rows)
        local_rows.extend(bib_local_rows)
        runtime_report["linked_bib"] = {
            "ref_bib_path": str(ref_bib),
            "entry_count": len(bib_public_rows),
            "resolved_pdf_count": sum(1 for row in bib_public_rows if row["attachment_status"] == "resolved"),
        }

    if ingest_mode in {"manual_pdf", "mixed"}:
        manual_public_rows, manual_local_rows = build_manual_pdf_entries(case_root, existing_status, local_rows + local_manifest.get("papers", []))
        public_rows.extend(manual_public_rows)
        local_rows.extend(manual_local_rows)
        runtime_report["manual_pdf_scan_count"] = len(manual_public_rows)

    public_manifest["papers"] = sorted(public_rows, key=lambda item: item["citation_key"])
    public_manifest["updated_at"] = runtime_report["updated_at"]
    local_manifest["papers"] = sorted(local_rows, key=lambda item: item["citation_key"])
    local_manifest["updated_at"] = runtime_report["updated_at"]

    write_json(paper_manifest_path(case_root), public_manifest)
    write_json(paper_manifest_local_path(case_root), local_manifest)
    write_json(case_root / "outputs" / "runtime" / "build_paper_manifest_report.json", runtime_report)

    print(f"Refreshed paper manifests for: {case_root}")
    print(f"Resolved papers: {sum(1 for row in public_manifest['papers'] if row['attachment_status'] == 'resolved')}")
    print(f"Unresolved papers: {sum(1 for row in public_manifest['papers'] if row['attachment_status'] == 'unresolved')}")


if __name__ == "__main__":
    main()
