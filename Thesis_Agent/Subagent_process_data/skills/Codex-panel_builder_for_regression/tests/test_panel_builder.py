from __future__ import annotations

import sys
import unittest
import shutil
from pathlib import Path


def _find_named_ancestor(path: Path, target_name: str) -> Path:
    for candidate in (path, *path.parents):
        if candidate.name == target_name:
            return candidate
    raise RuntimeError(f"could not locate ancestor named {target_name!r} from {path}")


ROOT = _find_named_ancestor(Path(__file__).resolve(), "Subagent_process_data")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_regression_panels import expand_combos, load_and_expand_spec, run_build


DEMO_CASE_ROOT = ROOT / "examples" / "_demo_thesis_case" / "_demo_provider_case"
DEMO_SPEC_PATH = DEMO_CASE_ROOT / "requests" / "demo_build_spec.json"


class PanelBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        output_root = DEMO_CASE_ROOT / "outputs"
        if output_root.exists():
            shutil.rmtree(output_root)
        source_catalog = (
            DEMO_CASE_ROOT
            / "fixtures"
            / "provider_catalogs"
            / "synthetic_demo"
            / "catalog.json"
        )
        target_catalog = (
            output_root
            / "specs"
            / "provider_catalogs"
            / "synthetic_demo"
            / "catalog.json"
        )
        target_catalog.parent.mkdir(parents=True, exist_ok=True)
        target_catalog.write_text(source_catalog.read_text(encoding="utf-8"), encoding="utf-8")

    def test_demo_provider_cartesian_spec(self) -> None:
        spec = load_and_expand_spec(DEMO_SPEC_PATH)
        combos = expand_combos(spec)
        self.assertEqual(len(combos), 2)

    def test_demo_build_outputs_manifest(self) -> None:
        result = run_build(load_and_expand_spec(DEMO_SPEC_PATH))
        self.assertEqual(result["panel_count"], 2)
        self.assertEqual(result["success_count"], 2)


if __name__ == "__main__":
    unittest.main()

