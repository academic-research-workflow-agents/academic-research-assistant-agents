from __future__ import annotations

import argparse
from pathlib import Path

from csv_to_latex import render_from_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Wrapper around csv_to_latex.py for manifest-driven asset rendering.")
    parser.add_argument("--case-root", required=True, help="Path to the writing case root.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    report_path = render_from_manifest(case_root)
    print(f"Rendered assets for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
