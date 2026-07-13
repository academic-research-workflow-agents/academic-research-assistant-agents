from __future__ import annotations

from pathlib import Path

from .base import CatalogProvider, load_catalog


PROVIDERS_ROOT = Path(__file__).resolve().parent


def _resolve_catalog_root(provider_id: str, case_root: Path | None) -> Path:
    if case_root is None:
        raise FileNotFoundError(f"case_root is required for provider {provider_id!r}")
    return case_root / "outputs" / "specs" / "provider_catalogs" / provider_id


def load_provider_catalog(provider_id: str, case_root: Path | None = None) -> dict:
    return load_catalog(_resolve_catalog_root(provider_id, case_root) / "catalog.json")


def load_provider(provider_id: str, case_root: Path | None = None) -> CatalogProvider:
    provider_root = _resolve_catalog_root(provider_id, case_root)
    catalog = load_provider_catalog(provider_id, case_root=case_root)
    asset_root = Path(case_root).resolve()
    return CatalogProvider(
        provider_id=provider_id,
        provider_root=provider_root,
        asset_root=asset_root,
        catalog=catalog,
    )
