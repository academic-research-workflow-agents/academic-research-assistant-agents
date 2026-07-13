from __future__ import annotations

import argparse
from pathlib import Path

from formatting_pipeline_lib import default_manifest, ensure_case_skeleton, source_manifest_path, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an empty layout-only case without正文 placeholders.")
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    ensure_case_skeleton(case_root)
    manifest_path = source_manifest_path(case_root)
    if manifest_path.exists() and not args.force:
        raise FileExistsError(f"Manifest already exists: {manifest_path}")
    write_json(manifest_path, default_manifest(case_root))
    print(f"Created layout-only case: {case_root}")


if __name__ == "__main__":
    main()
