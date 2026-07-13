from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MUNICIPALITY_NORMALIZE_MAP = {
    "110100": "110000",
    "120100": "120000",
    "310100": "310000",
    "500100": "500000"
}


def _read_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        frame = pd.read_excel(path)
    elif suffix == ".csv":
        frame = pd.read_csv(path, encoding="utf-8-sig")
    elif suffix == ".dta":
        frame = pd.read_stata(path, convert_categoricals=False)
    else:
        raise ValueError(f"Unsupported data file: {path}")
    frame.columns = [str(column).replace("\ufeff", "").strip() for column in frame.columns]
    return frame


def _normalize_municipality_codes(series: pd.Series) -> pd.Series:
    as_text = series.astype(str).str.replace(r"\.0$", "", regex=True)
    return as_text.replace(MUNICIPALITY_NORMALIZE_MAP)


def _apply_standardization(frame: pd.DataFrame, rules: list[str]) -> pd.DataFrame:
    output = frame.copy()
    for rule in rules:
        if rule == "normalize_entity_code":
            if "entity_key" in output.columns:
                output["entity_key"] = _normalize_municipality_codes(output["entity_key"])
            if "city_code" in output.columns:
                output["city_code"] = _normalize_municipality_codes(output["city_code"])
        elif rule == "stringify_entity_key":
            if "entity_key" in output.columns:
                output["entity_key"] = output["entity_key"].astype(str).str.replace(r"\.0$", "", regex=True)
        elif rule == "int_time_key":
            if "time_key" in output.columns:
                output["time_key"] = pd.to_numeric(output["time_key"], errors="coerce")
    return output


@dataclass(frozen=True)
class CatalogProvider:
    provider_id: str
    provider_root: Path
    asset_root: Path
    catalog: dict[str, Any]

    @property
    def source_assets(self) -> list[dict[str, Any]]:
        return list(self.catalog.get("source_assets", []))

    @property
    def candidate_variables(self) -> list[dict[str, Any]]:
        return list(self.catalog.get("candidate_variables", []))

    @property
    def control_bundles(self) -> list[dict[str, Any]]:
        return list(self.catalog.get("control_bundles", []))

    def get_source_asset(self, source_id: str) -> dict[str, Any]:
        for item in self.source_assets:
            if item["source_id"] == source_id:
                return dict(item)
        raise KeyError(f"Unknown source_id: {source_id}")

    def load_source_frame(self, source_id: str) -> pd.DataFrame:
        asset = self.get_source_asset(source_id)
        raw_path = asset.get("path")
        if not raw_path:
            raise ValueError(f"Source asset missing path: {source_id}")
        path = Path(raw_path)
        if not path.is_absolute():
            path = (self.asset_root / path).resolve()
        frame = _read_frame(path)
        rename_map = {}
        for canonical_name, source_name in dict(asset.get("key_columns", {})).items():
            rename_map[str(source_name)] = canonical_name
        for canonical_name, source_name in dict(asset.get("display_columns", {})).items():
            rename_map[str(source_name)] = canonical_name
        frame = frame.rename(columns=rename_map)
        frame = _apply_standardization(frame, list(asset.get("standardization", [])))
        missing_keys = [key for key in ("entity_key", "time_key") if key not in frame.columns]
        if missing_keys:
            raise ValueError(f"Source asset {source_id} missing canonical keys: {missing_keys}")
        return frame


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
