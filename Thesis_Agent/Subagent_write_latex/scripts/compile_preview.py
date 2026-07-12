from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from writing_pipeline_lib import (
    preview_dir,
    read_build_manifest_compatible,
    read_case_manifest_compatible,
    resolve_languages,
    runtime_dir,
    template_worktree_dir,
    utc_now_iso,
    write_build_manifest_compatible,
    write_json,
)


def ensure_tool(name: str) -> str:
    tool = shutil.which(name)
    if tool is None:
        raise RuntimeError(f"Required tool not found on PATH: {name}")
    return tool


def run_command(command: list[str], cwd: Path, log_path: Path) -> None:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    log_path.write_text((result.stdout or "") + "\n" + (result.stderr or ""), encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Command failed in {cwd}: {' '.join(command)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile the bilingual case-local literature-review preview.")
    parser.add_argument("--case-root", required=True, help="Path to the target review case root.")
    parser.add_argument("--language", default=None, help="Optional language override: zh or en.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    case_manifest = read_case_manifest_compatible(case_root)
    build_manifest = read_build_manifest_compatible(case_root, case_manifest)
    languages = resolve_languages(case_manifest, args.language)
    worktree = template_worktree_dir(case_root)
    if not worktree.exists():
        raise FileNotFoundError(f"Preview worktree does not exist: {worktree}")

    ensure_tool("xelatex")
    ensure_tool("biber")

    runtime_root = runtime_dir(case_root)
    runtime_root.mkdir(parents=True, exist_ok=True)
    compiled_outputs: list[str] = []
    compile_logs: list[str] = []
    preview_outputs: dict[str, str] = {}
    errors: list[dict[str, str]] = []

    for language in languages:
        compile_root = worktree / "parts" / language
        target_preview_dir = preview_dir(case_root, language)
        target_preview_dir.mkdir(parents=True, exist_ok=True)
        xelatex_cmd = ["xelatex", "-synctex=1", "-interaction=nonstopmode", "-file-line-error", "main.tex"]
        biber_cmd = ["biber", "main"]
        try:
            first_log = runtime_root / f"compile_preview_{language}_first.log"
            biber_log = runtime_root / f"compile_preview_{language}_biber.log"
            second_log = runtime_root / f"compile_preview_{language}_second.log"
            third_log = runtime_root / f"compile_preview_{language}_third.log"
            run_command(xelatex_cmd, compile_root, first_log)
            run_command(biber_cmd, compile_root, biber_log)
            run_command(xelatex_cmd, compile_root, second_log)
            run_command(xelatex_cmd, compile_root, third_log)
            preview_pdf = target_preview_dir / "lit_review_preview.pdf"
            shutil.copy2(compile_root / "main.pdf", preview_pdf)
            preview_outputs[language] = str(preview_pdf.relative_to(case_root)).replace("\\", "/")
            compiled_outputs.append(preview_outputs[language])
            compile_logs.extend(
                [
                    str(first_log.relative_to(case_root)).replace("\\", "/"),
                    str(biber_log.relative_to(case_root)).replace("\\", "/"),
                    str(second_log.relative_to(case_root)).replace("\\", "/"),
                    str(third_log.relative_to(case_root)).replace("\\", "/"),
                ]
            )
        except RuntimeError as exc:
            errors.append({"language": language, "error": str(exc)})

    build_manifest["compile_logs"] = compile_logs
    build_manifest["compiled_outputs"] = compiled_outputs
    build_manifest["preview_outputs"] = preview_outputs
    build_manifest["last_compiled_at"] = utc_now_iso()
    build_manifest["status"] = "compiled" if not errors else "compile_failed"
    write_build_manifest_compatible(case_root, case_manifest, build_manifest)

    report_path = runtime_root / "compile_preview_report.json"
    write_json(
        report_path,
        {
            "case_root": str(case_root),
            "preview_outputs": preview_outputs,
            "compile_logs": compile_logs,
            "errors": errors,
        },
    )
    if errors:
        raise RuntimeError(f"Preview compilation failed for {len(errors)} language(s). First failure: {errors[0]['language']} - {errors[0]['error']}")

    print(f"Compiled preview for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
