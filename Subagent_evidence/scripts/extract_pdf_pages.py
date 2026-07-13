from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader

from evidence_pipeline_lib import source_manifest_local_path, read_json, safe_output_stem, utc_now_iso


def resolve_pdf_path(case_root: Path, citation_key: str) -> Path:
    manifest = read_json(source_manifest_local_path(case_root), {"sources": []})
    for item in manifest.get("sources", []):
        if item.get("citation_key") == citation_key:
            pdf_path = item.get("resolved_pdf_path")
            if not pdf_path:
                raise FileNotFoundError(f"No resolved PDF path found for {citation_key}.")
            return Path(pdf_path)
    raise FileNotFoundError(f"Citation key not found in local manifest: {citation_key}")


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
) -> tuple[list[dict[str, object]], dict[str, object]]:
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
        return pages, {"ocr_used": False, "ocr_attempted": True}
    return ocr_pages, {"ocr_used": True, "ocr_engine": "rapidocr_onnxruntime", "ocr_attempted": True}


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a source PDF into page-level JSON and text.")
    parser.add_argument("--case-root", required=True, help="Path to the evidence case root.")
    parser.add_argument("--citation-key", required=True, help="Citation key to extract.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    citation_key = args.citation_key
    pdf_path = resolve_pdf_path(case_root, citation_key)
    pages = extract_pages(pdf_path)
    pages, ocr_meta = maybe_apply_ocr_fallback(pdf_path, pages)

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
        "extraction_method": "pypdf_with_ocr_fallback" if ocr_meta.get("ocr_used") else "pypdf",
        "pages": pages,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines: list[str] = []
    for page in pages:
        lines.append(f"===== PAGE {page['page_label']} =====")
        lines.append(str(page["text"]).strip())
        lines.append("")
    txt_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Extracted {len(pages)} pages for {citation_key}")
    if ocr_meta.get("ocr_used"):
        print("OCR fallback applied.")
    print(json_path)
    print(txt_path)


if __name__ == "__main__":
    main()
