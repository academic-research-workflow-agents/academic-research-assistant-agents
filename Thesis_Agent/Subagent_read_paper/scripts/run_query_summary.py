from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from reading_pipeline_lib import (
    case_manifest_path,
    evidence_ledger_path,
    filter_bib_entries,
    load_jsonl,
    normalize_info_tags,
    paper_manifest_path,
    query_manifest_path,
    read_json,
    resolve_case_path,
    slugify,
    write_json,
)

CANONICAL_INFO_TAGS = {"controls", "identification", "mechanism", "endogeneity", "sample", "outcome", "theme"}


def load_public_papers(case_root: Path) -> dict[str, dict[str, Any]]:
    manifest = read_json(paper_manifest_path(case_root), {"papers": []})
    return {item["citation_key"]: item for item in manifest.get("papers", [])}


def load_theme_lookup(case_root: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(case_root / "outputs" / "runtime" / "theme_index.json", {"papers": []})
    return {item["citation_key"]: item for item in payload.get("papers", [])}


def match_evidence_rows(rows: list[dict[str, Any]], normalized_tags: list[str]) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    canonical_only = all(tag in CANONICAL_INFO_TAGS for tag in normalized_tags)
    for row in rows:
        row_tags = normalize_info_tags(str(row.get("info_item", "")))
        if "theme" in row_tags and "theme" not in normalized_tags:
            continue
        haystack = " ".join(
            [
                str(row.get("info_item", "")),
                str(row.get("claim_summary", "")),
                str(row.get("verbatim_excerpt", "")),
            ]
        ).lower()
        if set(row_tags) & set(normalized_tags):
            matched.append(row)
            continue
        if not canonical_only and any(tag in haystack for tag in normalized_tags):
            matched.append(row)
    return matched


def write_summary(
    summary_path: Path,
    info_item: str,
    normalized_tags: list[str],
    papers: dict[str, dict[str, Any]],
    matched_rows: list[dict[str, Any]],
    theme_lookup: dict[str, dict[str, Any]],
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in matched_rows:
        groups.setdefault(str(row.get("citation_key")), []).append(row)

    lines = [
        f"# 信息条目：{info_item}",
        "",
        f"- 规范化标签：{', '.join(normalized_tags)}",
        f"- 命中论文数：{len(groups)}",
        f"- 命中证据条数：{len(matched_rows)}",
        "",
    ]
    if not matched_rows:
        lines.extend(
            [
                "## 当前结果",
                "",
                "当前 evidence ledger 里还没有命中这类信息的条目。",
                "请先补充对应论文的证据条目，或调整 query 的信息条目表述。",
            ]
        )
    else:
        theme_groups: dict[str, set[str]] = {}
        for citation_key in groups:
            theme_name = theme_lookup.get(citation_key, {}).get("primary_theme_group", "未分类")
            theme_groups.setdefault(str(theme_name), set()).add(citation_key)
        lines.extend(["## 按主题汇总", ""])
        for theme_name in sorted(theme_groups):
            lines.append(f"### {theme_name}")
            lines.append("")
            for citation_key in sorted(theme_groups[theme_name]):
                paper = papers.get(citation_key, {})
                theme_tags = theme_lookup.get(citation_key, {}).get("theme_tags", [])
                tag_text = ", ".join(f"`{tag}`" for tag in theme_tags)
                lines.append(f"- `{citation_key}` | {paper.get('title', citation_key)}")
                if tag_text:
                    lines.append(f"  - Theme Tags: {tag_text}")
            lines.append("")
        lines.extend(["## 按论文汇总", ""])
        for citation_key in sorted(groups):
            paper = papers.get(citation_key, {})
            lines.append(f"### {citation_key} | {paper.get('title', citation_key)}")
            lines.append("")
            for index, row in enumerate(groups[citation_key], start=1):
                lines.append(f"{index}. {row.get('claim_summary', '').strip()}")
                lines.append(f"   - 原文：{row.get('verbatim_excerpt', '').strip()}")
                lines.append(f"   - 页码：{row.get('page_span', '')}")
                lines.append(f"   - 证据来源：{row.get('source_card_md', '')}")
                lines.append("")
    summary_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_evidence_csv(csv_path: Path, matched_rows: list[dict[str, Any]], papers: dict[str, dict[str, Any]], theme_lookup: dict[str, dict[str, Any]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "citation_key",
        "paper_title",
        "primary_theme_group",
        "theme_tags",
        "source_card_md",
        "info_item",
        "claim_summary",
        "verbatim_excerpt",
        "page_span",
        "confidence",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in matched_rows:
            citation_key = str(row.get("citation_key", ""))
            writer.writerow(
                {
                    "citation_key": citation_key,
                    "paper_title": papers.get(citation_key, {}).get("title", citation_key),
                    "primary_theme_group": theme_lookup.get(citation_key, {}).get("primary_theme_group", ""),
                    "theme_tags": ", ".join(theme_lookup.get(citation_key, {}).get("theme_tags", [])),
                    "source_card_md": row.get("source_card_md", ""),
                    "info_item": row.get("info_item", ""),
                    "claim_summary": row.get("claim_summary", ""),
                    "verbatim_excerpt": row.get("verbatim_excerpt", ""),
                    "page_span": row.get("page_span", ""),
                    "confidence": row.get("confidence", ""),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a focused literature query from the evidence ledger.")
    parser.add_argument("--case-root", required=True, help="Path to the target reading case root.")
    parser.add_argument("--info-item", required=True, help="The query target, such as 控制变量 or 识别策略.")
    parser.add_argument("--query-id", default=None, help="Optional stable query id. Defaults to a slugified info item.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    query_id = args.query_id or slugify(args.info_item)
    normalized_tags = normalize_info_tags(args.info_item)
    query_dir = case_root / "outputs" / "queries" / query_id
    summary_path = query_dir / "summary.md"
    evidence_csv_path = query_dir / "evidence_list.csv"
    evidence_jsonl_path = query_dir / "evidence_list.jsonl"
    ref_v2_path = query_dir / "ref_v2.bib"

    papers = load_public_papers(case_root)
    theme_lookup = load_theme_lookup(case_root)
    evidence_rows = load_jsonl(evidence_ledger_path(case_root))
    matched_rows = match_evidence_rows(evidence_rows, normalized_tags)

    write_summary(summary_path, args.info_item, normalized_tags, papers, matched_rows, theme_lookup)
    write_evidence_csv(evidence_csv_path, matched_rows, papers, theme_lookup)
    evidence_jsonl_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in matched_rows) + ("\n" if matched_rows else ""),
        encoding="utf-8",
    )

    case_manifest = read_json(case_manifest_path(case_root), {})
    ref_bib = resolve_case_path(case_root, case_manifest.get("ref_bib_path"))
    selected_keys = sorted({str(row.get("citation_key")) for row in matched_rows if row.get("citation_key")})
    filter_bib_entries(ref_bib, selected_keys, ref_v2_path)

    query_manifest = {
        "schema_version": 1,
        "query_id": query_id,
        "info_item": args.info_item,
        "normalized_tags": normalized_tags,
        "selected_citation_keys": selected_keys,
        "summary_path": str(summary_path.resolve()),
        "evidence_list_path": str(evidence_csv_path.resolve()),
        "ref_v2_path": str(ref_v2_path.resolve()),
    }
    write_json(query_manifest_path(case_root, query_id), query_manifest)
    write_json(case_root / "outputs" / "runtime" / f"query_{query_id}_report.json", {"matched_rows": len(matched_rows), **query_manifest})

    print(f"Query summary generated for: {args.info_item}")
    print(f"Summary: {summary_path}")
    print(f"Evidence list: {evidence_csv_path}")
    print(f"ref_v2: {ref_v2_path}")


if __name__ == "__main__":
    main()
