from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_cache_id(value: object) -> str:
    text = str(value if value is not None else "default")
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return text[:80] or "default"


def read_excel_cached(
    path: Path,
    *,
    cache_root: Path,
    sheet_name: str | int | None = 0,
    dtype: object | None = object,
    usecols: object | None = None,
    engine: str | None = None,
    cache_name: str | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read Excel through a raw-hash cache without changing raw provenance."""
    path = path.resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    raw_hash = file_sha256(path)
    cache_id = cache_name or f"{path.stem}__sheet_{_safe_cache_id(sheet_name)}"
    if usecols is not None:
        cache_id = f"{cache_id}__usecols_{_safe_cache_id(usecols)}"
    cache_path = cache_root / f"{cache_id}.pkl"
    manifest_path = cache_root / f"{cache_id}_manifest.json"

    if cache_path.exists() and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            manifest = {}
        if (
            manifest.get("raw_sha256") == raw_hash
            and manifest.get("source_path") == path.as_posix()
            and manifest.get("sheet_name") == str(sheet_name)
            and manifest.get("usecols") == (str(usecols) if usecols is not None else None)
        ):
            return pd.read_pickle(cache_path)

    frame = pd.read_excel(path, sheet_name=sheet_name, dtype=dtype, usecols=usecols, engine=engine, **kwargs)
    frame.to_pickle(cache_path)
    manifest = {
        "source_path": path.as_posix(),
        "source_bytes": path.stat().st_size,
        "raw_sha256": raw_hash,
        "sheet_name": str(sheet_name),
        "usecols": str(usecols) if usecols is not None else None,
        "cache_path": cache_path.as_posix(),
        "created_at": datetime.now().isoformat(),
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": [str(column) for column in frame.columns],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return frame.copy()


def to_datetime_mixed(values: object) -> object:
    """Parse dates with strict pandas first, then recover failures via mixed format."""
    scalar_input = not isinstance(values, (pd.Series, list, tuple, pd.Index))
    series = pd.Series([values]) if scalar_input else pd.Series(values)
    strict = pd.to_datetime(series, errors="coerce")
    mask = strict.isna() & series.notna() & series.astype(str).str.strip().ne("")
    if mask.any():
        try:
            recovered = pd.to_datetime(series.loc[mask], errors="coerce", format="mixed")
        except (TypeError, ValueError):
            recovered = pd.to_datetime(series.loc[mask], errors="coerce", infer_datetime_format=True)
        strict.loc[mask] = recovered
    if scalar_input:
        return strict.iloc[0]
    return strict


def date_parse_recoverability_summary(values: object, *, field_name: str) -> dict[str, object]:
    series = pd.Series(values)
    strict = pd.to_datetime(series, errors="coerce")
    mixed = to_datetime_mixed(series)
    nonempty = series.notna() & series.astype(str).str.strip().ne("")
    recoverable = strict.isna() & pd.Series(mixed).notna()
    samples = series.loc[recoverable].astype(str).drop_duplicates().head(20).tolist()
    return {
        "field_name": field_name,
        "row_count": int(len(series)),
        "raw_nonempty_count": int(nonempty.sum()),
        "strict_success_count": int(strict.notna().sum()),
        "mixed_success_count": int(pd.Series(mixed).notna().sum()),
        "recoverable_count": int(recoverable.sum()),
        "sample_recoverable_values": samples,
    }
