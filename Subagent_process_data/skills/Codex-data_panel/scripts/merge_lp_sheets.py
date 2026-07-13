from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from lp_pipeline_utils import EXPECTED_COLUMNS, load_workbook_sheets, write_xlsx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge all sheets from the LP workbook into one xlsx file.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--delete-source", action="store_true", help="Delete the original workbook after merge.")
    return parser.parse_args()


def build_output_path(input_path: Path, output_dir: Path) -> Path:
    stem = input_path.stem
    return output_dir / f"{stem}_merged.xlsx"


def main() -> None:
    args = parse_args()
    input_path = args.input_path.resolve()
    output_dir = args.output_dir.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Workbook not found: {input_path}")

    sheet_names, frames = load_workbook_sheets(input_path)
    if not frames:
        raise ValueError("No sheets found in workbook")

    merged = pd.concat(frames, ignore_index=True)
    if list(merged.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected merged columns: {list(merged.columns)}")

    output_path = build_output_path(input_path, output_dir)
    write_xlsx(merged, output_path, sheet_name="LP_merged")

    merged_check = pd.read_excel(output_path, dtype=object)
    if len(merged_check) != len(merged):
        raise ValueError("Merged row count validation failed")

    expected_rows = sum(len(frame) for frame in frames)
    if expected_rows != len(merged):
        raise ValueError("Source sheet row count validation failed")

    output_dir.mkdir(parents=True, exist_ok=True)
    if args.delete_source:
        input_path.unlink()

    print(f"sheets={len(sheet_names)} rows={len(merged)} output={output_path}")


if __name__ == "__main__":
    main()
