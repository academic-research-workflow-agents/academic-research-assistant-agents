from __future__ import annotations

import argparse
from pathlib import Path

from lp_pipeline_utils import EXPECTED_COLUMNS, FUND_NAME_COL, LP_COL, load_merged_dataset, to_panel, write_xlsx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert merged LP data to panel format.")
    parser.add_argument("--merged-path", type=Path, required=True)
    parser.add_argument("--panel-dir", type=Path, required=True)
    parser.add_argument("--exceptions-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merged_path = args.merged_path.resolve()
    panel_dir = args.panel_dir.resolve()
    exceptions_dir = args.exceptions_dir.resolve()
    frame = load_merged_dataset(merged_path)

    non_null_names = frame[FUND_NAME_COL].dropna().astype(str)
    duplicate_names = non_null_names[non_null_names.duplicated()].unique().tolist()
    if duplicate_names:
        raise ValueError(f"Fund name is not unique: {duplicate_names[:5]}")

    panel, exceptions = to_panel(frame)
    if list(panel.columns) != EXPECTED_COLUMNS or list(exceptions.columns) != EXPECTED_COLUMNS:
        raise ValueError("Output columns do not match expected structure")

    panel_path = panel_dir / merged_path.name.replace("_merged.xlsx", "_panel.xlsx")
    exceptions_path = exceptions_dir / merged_path.name.replace("_merged.xlsx", "_exceptions.xlsx")

    panel_dir.mkdir(parents=True, exist_ok=True)
    exceptions_dir.mkdir(parents=True, exist_ok=True)
    write_xlsx(panel, panel_path, sheet_name="LP_panel")
    write_xlsx(exceptions, exceptions_path, sheet_name="LP_exceptions")

    if len(exceptions) != 14:
        raise ValueError(f"Expected 14 exception rows, got {len(exceptions)}")

    lp_rows = panel[LP_COL].notna().sum()
    if lp_rows == 0:
        raise ValueError("Panel data does not contain LP rows")

    print(f"panel_rows={len(panel)} exception_rows={len(exceptions)} panel={panel_path} exceptions={exceptions_path}")


if __name__ == "__main__":
    main()
