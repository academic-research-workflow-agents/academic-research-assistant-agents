from __future__ import annotations

import argparse
from pathlib import Path

from integration_lib import build_scan_payload, resolve_existing_case_root, scan_json_path, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan linked business cases for the current research_case.")
    parser.add_argument("--case-root", help="Path to the integration child_case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve() if args.case_root else resolve_existing_case_root()
    payload = build_scan_payload(case_root)
    target = scan_json_path(case_root)
    write_json(target, payload)
    print(f"Scan report: {target}")


if __name__ == "__main__":
    main()
