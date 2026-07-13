from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


BRAND_COL = "引导基金品牌"
FUND_NAME_COL = "引导基金名称"
LP_COL = "最近合作LP"
EXPECTED_COLUMNS = [
    BRAND_COL,
    FUND_NAME_COL,
    "成立时间",
    "注册地区",
    "注册资本",
    LP_COL,
    "基金级别",
]
MISSING_LITERALS = {"", "nan", "none", "--"}


def standardize_columns(columns: Iterable[object]) -> list[str]:
    return [str(col).replace("\ufeff", "").strip() for col in columns]


def normalize_missing(series: pd.Series) -> pd.Series:
    as_string = series.astype(str).str.strip().str.lower()
    mask = series.isna() | as_string.isin(MISSING_LITERALS)
    return series.mask(mask, pd.NA)


def load_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    frame = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
    frame.columns = standardize_columns(frame.columns)
    missing = [col for col in EXPECTED_COLUMNS if col not in frame.columns]
    if missing:
        raise KeyError(f"{sheet_name} is missing required columns: {missing}")
    frame = frame[EXPECTED_COLUMNS].copy()
    for column in frame.columns:
        frame[column] = normalize_missing(frame[column])
    return frame


def load_workbook_sheets(path: Path) -> tuple[list[str], list[pd.DataFrame]]:
    excel = pd.ExcelFile(path)
    sheet_names = excel.sheet_names
    frames = [load_sheet(path, sheet_name) for sheet_name in sheet_names]
    return sheet_names, frames


def load_merged_dataset(path: Path) -> pd.DataFrame:
    frame = pd.read_excel(path, dtype=object)
    frame.columns = standardize_columns(frame.columns)
    frame = frame[EXPECTED_COLUMNS].copy()
    for column in frame.columns:
        frame[column] = normalize_missing(frame[column])
    return frame


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_xlsx(frame: pd.DataFrame, output_path: Path, sheet_name: str = "Sheet1") -> None:
    ensure_parent_dir(output_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet_name)


def is_brand_only_exception(frame: pd.DataFrame) -> pd.Series:
    other_cols = [col for col in EXPECTED_COLUMNS if col != BRAND_COL]
    return frame[BRAND_COL].notna() & frame[other_cols].isna().all(axis=1)


def to_panel(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    exception_mask = is_brand_only_exception(frame)
    exceptions = frame.loc[exception_mask, EXPECTED_COLUMNS].reset_index(drop=True)

    panel = frame.loc[~exception_mask, EXPECTED_COLUMNS].copy()
    fill_cols = [col for col in EXPECTED_COLUMNS if col != LP_COL]
    latest_fund_row: dict[str, object] | None = None

    for index, row in panel.iterrows():
        has_fund_name = pd.notna(row[FUND_NAME_COL])
        has_lp = pd.notna(row[LP_COL])

        if has_fund_name:
            latest_fund_row = {
                col: row[col]
                for col in fill_cols
            }
            continue

        if has_lp and latest_fund_row is not None:
            for col in fill_cols:
                panel.at[index, col] = latest_fund_row[col]

    panel = panel.reset_index(drop=True)
    return panel, exceptions
