from __future__ import annotations

import argparse
from pathlib import Path

from integration_lib import (
    build_coordination_manifest,
    build_coordination_report,
    manifest_path,
    report_md_path,
    resolve_existing_case_root,
    write_json,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh research_coordination_manifest.json for the current integration case.")
    parser.add_argument("--case-root", help="Path to the integration child_case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve() if args.case_root else resolve_existing_case_root()
    manifest = build_coordination_manifest(case_root)
    write_json(manifest_path(case_root), manifest)
    write_text(report_md_path(case_root), build_coordination_report(manifest))
    print(f"Manifest refreshed: {manifest_path(case_root)}")
    print(f"Report: {report_md_path(case_root)}")


if __name__ == "__main__":
    main()
