from __future__ import annotations

import runpy
from pathlib import Path


def _find_named_ancestor(path: Path, target_name: str) -> Path:
    for candidate in (path, *path.parents):
        if candidate.name == target_name:
            return candidate
    raise RuntimeError(f"could not locate ancestor named {target_name!r} from {path}")


SUBAGENT_ROOT = _find_named_ancestor(Path(__file__).resolve(), "Subagent_process_data")
SCRIPT_PATH = SUBAGENT_ROOT / "scripts" / "build_regression_panels.py"


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
