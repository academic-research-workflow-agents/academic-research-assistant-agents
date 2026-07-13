from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from formatting_pipeline_lib import load_manifest, resolve_declared_path, safe_output_path, sha256_file, write_json


def convert_markdown(source: Path, target: Path) -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required for declared Markdown sources.")
    result = subprocess.run(
        [pandoc, "--from=gfm", "--to=latex", "--wrap=none", str(source)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Pandoc conversion failed.")
    target.write_text(result.stdout, encoding="utf-8")
    return "pandoc:gfm-to-latex"


def convert_case(case_root: Path) -> dict:
    manifest = load_manifest(case_root)
    seen_ids: set[str] = set()
    report = {"schema_version": 1, "case_id": manifest["case_id"], "status": "pass", "processed": []}
    for item in manifest.get("sources", []):
        source_id = str(item["id"])
        if source_id in seen_ids:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen_ids.add(source_id)
        source = resolve_declared_path(case_root, str(item["path"]), ("inputs",))
        if not source.is_file():
            raise FileNotFoundError(f"Declared source does not exist: {source}")
        target = safe_output_path(case_root, str(item["target"]), "formatted")
        target.parent.mkdir(parents=True, exist_ok=True)
        if item["format"] == "latex":
            shutil.copyfile(source, target)
            converter = "byte-copy"
        elif item["format"] == "markdown":
            converter = convert_markdown(source, target)
        else:
            raise ValueError(f"Unsupported source format: {item['format']}")
        report["processed"].append(
            {
                "id": source_id,
                "input": item["path"],
                "output": str(target.relative_to(case_root)).replace("\\", "/"),
                "input_sha256": sha256_file(source),
                "output_sha256": sha256_file(target),
                "converter": converter,
            }
        )
    report_path = case_root / "outputs" / "runtime" / "source_conversion_report.json"
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert only manifest-declared user sources to LaTeX.")
    parser.add_argument("--case-root", required=True)
    args = parser.parse_args()
    report = convert_case(Path(args.case_root).resolve())
    print(f"Processed sources: {len(report['processed'])}")


if __name__ == "__main__":
    main()
