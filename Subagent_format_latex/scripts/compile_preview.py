from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from formatting_pipeline_lib import load_manifest, safe_output_path, write_json


def compile_preview(case_root: Path) -> dict:
    manifest = load_manifest(case_root)
    entrypoint = manifest.get("entrypoint")
    if not entrypoint:
        raise ValueError("source_manifest.entrypoint is required for preview compilation.")
    formatted_root = (case_root / "outputs" / "build" / "formatted").resolve()
    source_entrypoint = safe_output_path(case_root, str(entrypoint), "formatted")
    if not source_entrypoint.is_file():
        raise FileNotFoundError("Run convert_sources_to_latex.py before compiling the preview.")
    worktree = case_root / "outputs" / "build" / "preview-worktree"
    latex_output = case_root / "outputs" / "build" / "latex"
    for directory in (worktree, latex_output):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copytree(formatted_root, worktree, dirs_exist_ok=True)
    assets_root = case_root / "outputs" / "build" / "assets"
    if assets_root.exists():
        shutil.copytree(assets_root, worktree / "assets", dirs_exist_ok=True)
    latexmk = shutil.which("latexmk")
    if not latexmk:
        raise RuntimeError("latexmk is required for preview compilation.")
    result = subprocess.run(
        [latexmk, "-xelatex", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={latex_output}", Path(entrypoint).name],
        cwd=worktree,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    pdf_source = latex_output / (Path(entrypoint).stem + ".pdf")
    pdf_target = case_root / "outputs" / "preview" / f"{manifest['case_id']}.pdf"
    if result.returncode == 0 and pdf_source.exists():
        pdf_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf_source, pdf_target)
    report = {
        "schema_version": 1,
        "case_id": manifest["case_id"],
        "status": "pass" if result.returncode == 0 else "fail",
        "entrypoint": entrypoint,
        "pdf": str(pdf_target.relative_to(case_root)).replace("\\", "/") if pdf_target.exists() else None,
        "returncode": result.returncode,
    }
    write_json(case_root / "outputs" / "runtime" / "compile_preview_report.json", report)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "LaTeX compilation failed.")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a preview from converted user sources.")
    parser.add_argument("--case-root", required=True)
    args = parser.parse_args()
    report = compile_preview(Path(args.case_root).resolve())
    print(report["pdf"])


if __name__ == "__main__":
    main()
