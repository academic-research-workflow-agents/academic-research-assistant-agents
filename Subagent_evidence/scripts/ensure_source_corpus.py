from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from evidence_pipeline_lib import source_manifest_local_path, source_manifest_path, read_json, safe_output_stem, utc_now_iso, write_json


def load_public_sources(case_root: Path) -> list[dict[str, Any]]:
    payload = read_json(source_manifest_path(case_root), {"sources": []})
    return list(payload.get("sources", []))


def load_local_sources(case_root: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(source_manifest_local_path(case_root), {"sources": []})
    return {str(item.get("citation_key")): item for item in payload.get("sources", [])}


def load_existing_metrics(json_path: Path) -> dict[str, Any]:
    payload = read_json(json_path, {})
    if not payload:
        return {}
    pages = payload.get("pages", [])
    total_chars = sum(len(str(page.get("text", ""))) for page in pages)
    nonempty_pages = sum(1 for page in pages if str(page.get("text", "")).strip())
    return {
        "page_count": payload.get("page_count", len(pages)),
        "nonempty_pages": nonempty_pages,
        "total_chars": total_chars,
        "generated_at": payload.get("generated_at", ""),
    }


def extract_pages(pdf_path: Path) -> list[dict[str, object]]:
    reader = PdfReader(str(pdf_path))
    pages: list[dict[str, object]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(
            {
                "page_index": index,
                "page_label": str(index),
                "text": text,
            }
        )
    return pages


def page_metrics(pages: list[dict[str, object]]) -> dict[str, int]:
    total_chars = sum(len(str(page.get("text", ""))) for page in pages)
    nonempty_pages = sum(1 for page in pages if str(page.get("text", "")).strip())
    return {
        "page_count": len(pages),
        "nonempty_pages": nonempty_pages,
        "total_chars": total_chars,
    }


def maybe_apply_ocr_fallback(
    pdf_path: Path,
    pages: list[dict[str, object]],
    *,
    min_total_chars: int = 500,
    min_page_chars: int = 40,
    zoom: float = 2.0,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    metrics = page_metrics(pages)
    if metrics["total_chars"] >= min_total_chars and metrics["nonempty_pages"] > 0:
        return pages, {"ocr_used": False}

    try:
        import fitz
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # pragma: no cover - optional runtime dependency
        return pages, {"ocr_used": False, "ocr_error": f"{type(exc).__name__}: {exc}"}

    ocr = RapidOCR()
    document = fitz.open(str(pdf_path))
    ocr_pages: list[dict[str, object]] = []
    replaced_pages = 0
    filled_blank_pages = 0

    try:
        for index, pdf_page in enumerate(document, start=1):
            original_text = ""
            if index - 1 < len(pages):
                original_text = str(pages[index - 1].get("text", "") or "")

            pix = pdf_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            result, _ = ocr(image)
            ocr_lines = [str(item[1]).strip() for item in (result or []) if len(item) > 1 and str(item[1]).strip()]
            ocr_text = "\n".join(ocr_lines).strip()

            chosen_text = original_text
            if len(original_text.strip()) < min_page_chars and len(ocr_text) > len(original_text.strip()):
                chosen_text = ocr_text
                replaced_pages += 1
                if not original_text.strip() and ocr_text:
                    filled_blank_pages += 1

            ocr_pages.append(
                {
                    "page_index": index,
                    "page_label": str(index),
                    "text": chosen_text,
                }
            )
    finally:
        document.close()

    ocr_metrics = page_metrics(ocr_pages)
    if ocr_metrics["total_chars"] <= metrics["total_chars"]:
        return pages, {"ocr_used": False, "ocr_attempted": True, "ocr_total_chars": ocr_metrics["total_chars"]}

    metadata: dict[str, Any] = {
        "ocr_used": True,
        "ocr_engine": "rapidocr_onnxruntime",
        "ocr_attempted": True,
        "ocr_replaced_pages": replaced_pages,
        "ocr_filled_blank_pages": filled_blank_pages,
        "ocr_total_chars": ocr_metrics["total_chars"],
    }
    return ocr_pages, metadata


def write_fulltext_payload(
    case_root: Path,
    citation_key: str,
    pdf_path: Path,
    pages: list[dict[str, object]],
    *,
    extraction_method: str = "pypdf",
) -> dict[str, Any]:
    out_dir = case_root / "outputs" / "runtime" / "fulltext"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_stem = safe_output_stem(citation_key)
    json_path = out_dir / f"{output_stem}.pages.json"
    txt_path = out_dir / f"{output_stem}.pages.txt"

    payload = {
        "schema_version": 1,
        "citation_key": citation_key,
        "source_pdf": str(pdf_path),
        "page_count": len(pages),
        "generated_at": utc_now_iso(),
        "extraction_method": extraction_method,
        "pages": pages,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines: list[str] = []
    for page in pages:
        lines.append(f"===== PAGE {page['page_label']} =====")
        lines.append(str(page["text"]).strip())
        lines.append("")
    txt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    metrics = page_metrics(pages)
    return {
        "json_path": str(json_path.resolve()),
        "txt_path": str(txt_path.resolve()),
        "page_count": metrics["page_count"],
        "nonempty_pages": metrics["nonempty_pages"],
        "total_chars": metrics["total_chars"],
    }


def summarize_status(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("fulltext_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def inventory_markdown(rows: list[dict[str, Any]], summary: dict[str, int]) -> str:
    lines = [
        "# Fulltext Inventory",
        "",
        f"- Generated at: {utc_now_iso()}",
        f"- Total sources: {len(rows)}",
        "",
        "## Status Summary",
        "",
    ]
    for key in sorted(summary):
        lines.append(f"- `{key}`: {summary[key]}")
    lines.extend(["", "## Source Inventory", ""])
    for row in rows:
        lines.append(f"- `{row['citation_key']}` | {row['title']}")
        lines.append(f"  - fulltext_status: `{row['fulltext_status']}`")
        lines.append(f"  - page_count: `{row['page_count']}` | nonempty_pages: `{row['nonempty_pages']}` | total_chars: `{row['total_chars']}`")
        lines.append(f"  - note: {row['note']}")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensure page-level fulltext extraction exists for all sources in a evidence case.")
    parser.add_argument("--case-root", required=True, help="Path to the evidence case root.")
    parser.add_argument("--force", action="store_true", help="Re-extract even when JSON/TXT outputs already exist.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    public_rows = load_public_sources(case_root)
    local_rows = load_local_sources(case_root)
    out_dir = case_root / "outputs" / "runtime" / "fulltext"
    out_dir.mkdir(parents=True, exist_ok=True)

    inventory: list[dict[str, Any]] = []
    for public_row in public_rows:
        citation_key = str(public_row.get("citation_key", ""))
        title = str(public_row.get("title", citation_key))
        local_row = local_rows.get(citation_key, {})
        pdf_value = local_row.get("resolved_pdf_path")
        row: dict[str, Any] = {
            "citation_key": citation_key,
            "title": title,
            "resolved_pdf_path": str(pdf_value) if pdf_value else "",
            "fulltext_status": "missing",
            "page_count": 0,
            "nonempty_pages": 0,
            "total_chars": 0,
            "json_path": "",
            "txt_path": "",
            "note": "missing",
        }
        if not pdf_value:
            row["fulltext_status"] = "missing_pdf_path"
            row["note"] = "source_manifest.private.json 中没有 resolved_pdf_path。"
            inventory.append(row)
            continue

        pdf_path = Path(str(pdf_value))
        if not pdf_path.exists():
            row["fulltext_status"] = "missing_pdf_file"
            row["note"] = "resolved_pdf_path 指向的 PDF 不存在。"
            inventory.append(row)
            continue

        json_path = out_dir / f"{citation_key}.pages.json"
        txt_path = out_dir / f"{citation_key}.pages.txt"
        safe_stem = safe_output_stem(citation_key)
        safe_json_path = out_dir / f"{safe_stem}.pages.json"
        safe_txt_path = out_dir / f"{safe_stem}.pages.txt"
        if not json_path.exists() and safe_json_path.exists():
            json_path = safe_json_path
        if not txt_path.exists() and safe_txt_path.exists():
            txt_path = safe_txt_path
        if not args.force and json_path.exists() and txt_path.exists():
            metrics = load_existing_metrics(json_path)
            if metrics.get("total_chars", 0) == 0:
                try:
                    pages = extract_pages(pdf_path)
                    pages, ocr_meta = maybe_apply_ocr_fallback(pdf_path, pages)
                    if ocr_meta.get("ocr_used"):
                        refreshed = write_fulltext_payload(
                            case_root,
                            citation_key,
                            pdf_path,
                            pages,
                            extraction_method="pypdf_with_ocr_fallback",
                        )
                        row.update(refreshed)
                        row["fulltext_status"] = "existing_ocr_refreshed"
                        row["note"] = (
                            "现有全文文件文本为空，已用 OCR fallback 重建页级全文。"
                            f" filled_blank_pages={ocr_meta.get('ocr_filled_blank_pages', 0)}"
                        )
                        inventory.append(row)
                        continue
                except Exception as exc:  # pragma: no cover - runtime diagnostics
                    row["ocr_note"] = f"{type(exc).__name__}: {exc}"
            row.update(
                {
                    "fulltext_status": "existing" if metrics.get("total_chars", 0) > 0 else "existing_low_text",
                    "page_count": metrics.get("page_count", 0),
                    "nonempty_pages": metrics.get("nonempty_pages", 0),
                    "total_chars": metrics.get("total_chars", 0),
                    "json_path": str(json_path.resolve()),
                    "txt_path": str(txt_path.resolve()),
                    "note": "沿用现有全文抽取结果。" if metrics.get("total_chars", 0) > 0 else "现有全文文件存在，但文本量偏低。",
                }
            )
            inventory.append(row)
            continue

        try:
            pages = extract_pages(pdf_path)
            pages, ocr_meta = maybe_apply_ocr_fallback(pdf_path, pages)
            metrics = write_fulltext_payload(
                case_root,
                citation_key,
                pdf_path,
                pages,
                extraction_method="pypdf_with_ocr_fallback" if ocr_meta.get("ocr_used") else "pypdf",
            )
            row.update(metrics)
            if metrics["page_count"] == 0 or metrics["total_chars"] == 0:
                row["fulltext_status"] = "extracted_empty"
                row["note"] = "PDF 已抽取，但未获得可用文本。"
            elif metrics["nonempty_pages"] == 0:
                row["fulltext_status"] = "extracted_blank"
                row["note"] = "PDF 已抽取，但所有页面文本为空。"
            elif metrics["total_chars"] < 500:
                row["fulltext_status"] = "extracted_low_text"
                row["note"] = "PDF 已抽取，但文本量较低，后续需要人工核查。"
            else:
                row["fulltext_status"] = "extracted_ocr" if ocr_meta.get("ocr_used") else "extracted"
                if ocr_meta.get("ocr_used"):
                    row["note"] = (
                        "PDF 页级全文抽取完成，并对低文本页面启用了 OCR fallback。"
                        f" filled_blank_pages={ocr_meta.get('ocr_filled_blank_pages', 0)}"
                    )
                else:
                    row["note"] = "PDF 页级全文抽取完成。"
            if ocr_meta.get("ocr_error"):
                row["ocr_note"] = str(ocr_meta["ocr_error"])
        except Exception as exc:  # pragma: no cover - runtime diagnostics
            row["fulltext_status"] = "extract_error"
            row["note"] = f"{type(exc).__name__}: {exc}"
        inventory.append(row)

    inventory.sort(key=lambda item: item["citation_key"])
    summary = summarize_status(inventory)
    report = {
        "schema_version": 1,
        "generated_at": utc_now_iso(),
        "case_root": str(case_root),
        "total_sources": len(inventory),
        "status_summary": summary,
        "sources": inventory,
    }
    write_json(case_root / "outputs" / "runtime" / "fulltext_inventory.json", report)
    (case_root / "outputs" / "runtime" / "fulltext_inventory.md").write_text(inventory_markdown(inventory, summary), encoding="utf-8")

    print(f"Fulltext inventory generated for: {case_root}")
    print(f"Total sources: {len(inventory)}")
    for key in sorted(summary):
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
