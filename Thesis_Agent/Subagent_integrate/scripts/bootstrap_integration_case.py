from __future__ import annotations

import argparse
from pathlib import Path

from integration_lib import (
    default_case_agents,
    default_case_readme,
    default_coordination_manifest,
    ensure_case_skeleton,
    manifest_path,
    report_md_path,
    resolve_existing_case_root,
    write_json,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap an integration child_case.")
    parser.add_argument("--case-root", help="Path to the integration child_case root.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing manifest and entry docs.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve() if args.case_root else resolve_existing_case_root()
    ensure_case_skeleton(case_root)

    agents_path = case_root / "AGENTS.md"
    readme_path = case_root / "README.md"
    manifest_file = manifest_path(case_root)
    report_file = report_md_path(case_root)

    if args.force or not agents_path.exists():
        write_text(agents_path, default_case_agents(case_root.name))
    if args.force or not readme_path.exists():
        write_text(readme_path, default_case_readme(case_root.name))
    if args.force or not manifest_file.exists():
        write_json(manifest_file, default_coordination_manifest(case_root))
    if args.force or not report_file.exists():
        write_text(report_file, "# Thesis Coordination Report\n\nBootstrap completed.\n")

    print(f"Bootstrapped integration case: {case_root}")
    print(f"Manifest: {manifest_file}")


if __name__ == "__main__":
    main()
