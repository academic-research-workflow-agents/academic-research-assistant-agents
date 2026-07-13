from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from formatting_pipeline_lib import load_manifest, resolve_declared_path, safe_output_path, sha256_file, write_json


LATEX_REPLACEMENTS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}


def latex_escape(value: str) -> str:
    return "".join(LATEX_REPLACEMENTS.get(char, char) for char in value)


def csv_to_tabular(source: Path) -> str:
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows or not rows[0]:
        raise ValueError(f"Declared CSV table is empty: {source}")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"Declared CSV table has inconsistent row widths: {source}")
    lines = [rf"\begin{{tabular}}{{{'l' * width}}}"]
    lines.extend(" & ".join(latex_escape(cell) for cell in row) + r" \\" for row in rows)
    lines.append(r"\end{tabular}")
    return "\n".join(lines) + "\n"


def materialize(case_root: Path) -> dict:
    manifest = load_manifest(case_root)
    report = {"schema_version": 1, "case_id": manifest["case_id"], "status": "pass", "processed": []}
    for item in manifest.get("assets", []):
        source = resolve_declared_path(case_root, str(item["path"]), ("inputs", "assets"))
        if not source.is_file():
            raise FileNotFoundError(f"Declared asset does not exist: {source}")
        target = safe_output_path(case_root, str(item["target"]), "assets")
        target.parent.mkdir(parents=True, exist_ok=True)
        if item["kind"] == "csv_table":
            target.write_text(csv_to_tabular(source), encoding="utf-8")
            operation = "csv-to-tabular"
        else:
            shutil.copyfile(source, target)
            operation = "byte-copy"
        report["processed"].append(
            {
                "id": item["id"],
                "kind": item["kind"],
                "input": item["path"],
                "output": str(target.relative_to(case_root)).replace("\\", "/"),
                "input_sha256": sha256_file(source),
                "output_sha256": sha256_file(target),
                "operation": operation,
            }
        )
    write_json(case_root / "outputs" / "runtime" / "asset_materialization_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize only manifest-declared layout assets.")
    parser.add_argument("--case-root", required=True)
    args = parser.parse_args()
    report = materialize(Path(args.case_root).resolve())
    print(f"Processed assets: {len(report['processed'])}")


if __name__ == "__main__":
    main()
