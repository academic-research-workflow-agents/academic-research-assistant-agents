from __future__ import annotations

import argparse
from pathlib import Path

from evidence_pipeline_lib import (
    WORKSPACE_ROOT,
    case_manifest_path,
    default_case_agents,
    default_case_manifest,
    default_case_readme,
    default_source_manifest,
    default_source_manifest_local,
    detect_default_ingest_mode,
    ensure_case_skeleton,
    ensure_text,
    evidence_ledger_path,
    normalize_ingest_mode,
    source_manifest_local_path,
    source_manifest_path,
    relpath_from,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a evidence-layer case.")
    parser.add_argument("--case-root", required=True, help="Path to the target evidence case root.")
    parser.add_argument(
        "--ingest-mode",
        default=None,
        help="linked_bib, manual_pdf, or mixed. Defaults to workspace-aware auto detection.",
    )
    parser.add_argument(
        "--ref-bib",
        default=None,
        help="Optional ref.bib path. If omitted, use workspace root ref.bib when available; otherwise use inputs/ref/ref_v1.bib.",
    )
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    ensure_case_skeleton(case_root)

    ingest_mode = normalize_ingest_mode(args.ingest_mode or detect_default_ingest_mode(WORKSPACE_ROOT))
    if args.ref_bib:
        requested_ref = Path(args.ref_bib)
        if requested_ref.is_absolute():
            ref_bib_path = relpath_from(case_root, requested_ref)
        else:
            requested_from_cwd = (Path.cwd() / requested_ref).resolve()
            ref_bib_path = relpath_from(case_root, requested_from_cwd) if requested_from_cwd.exists() else args.ref_bib
    else:
        workspace_bib = WORKSPACE_ROOT / "ref.bib"
        ref_bib_path = relpath_from(case_root, workspace_bib) if workspace_bib.exists() else "inputs/ref/ref_v1.bib"

    write_json(case_manifest_path(case_root), default_case_manifest(case_root, ingest_mode, ref_bib_path))
    write_json(source_manifest_path(case_root), default_source_manifest(case_root))
    write_json(source_manifest_local_path(case_root), default_source_manifest_local(case_root))

    ensure_text(case_root / "AGENTS.md", default_case_agents(case_root.name), overwrite=False)
    ensure_text(case_root / "README.md", default_case_readme(case_root.name, ingest_mode, ref_bib_path), overwrite=False)
    ensure_text(case_root / "requests" / "README.md", "在这里记录阅读任务、查询请求和用户确认事项。\n", overwrite=False)
    ensure_text(case_root / "evidence_cards" / "README.md", "每篇学术来源一张卡，文件名建议为 <citation_key>.md。\n", overwrite=False)
    if not evidence_ledger_path(case_root).exists():
        evidence_ledger_path(case_root).write_text("", encoding="utf-8")

    print(f"Bootstrapped evidence case: {case_root}")
    print(f"Ingest mode: {ingest_mode}")
    print(f"ref_bib_path: {ref_bib_path}")


if __name__ == "__main__":
    main()
