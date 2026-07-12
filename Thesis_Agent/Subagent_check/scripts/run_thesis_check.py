from __future__ import annotations

import argparse
from pathlib import Path

from check_lib import (
    build_markdown_report,
    manifest_path,
    report_json_path,
    report_md_path,
    resolve_existing_case_root,
    run_check,
    write_json,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a thesis-wide read-only check and write the report into the current check case.")
    parser.add_argument("--case-root", help="Path to the check child_case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve() if args.case_root else resolve_existing_case_root()
    report = run_check(case_root)
    detail_outputs = list(report.pop("detail_outputs_to_write", []) or [])
    for item in detail_outputs:
        output_path = case_root / str(item.get("path") or "")
        kind = str(item.get("kind") or "json")
        if kind == "json":
            write_json(output_path, item.get("content"))
        else:
            write_text(output_path, str(item.get("content") or ""))
    write_json(report_json_path(case_root), report)
    write_text(report_md_path(case_root), build_markdown_report(report))
    write_json(manifest_path(case_root), report["updated_check_manifest"])
    print(f"Check report: {report_json_path(case_root)}")
    print(f"Markdown report: {report_md_path(case_root)}")


if __name__ == "__main__":
    main()
