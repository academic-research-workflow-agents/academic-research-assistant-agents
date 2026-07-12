from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path
from typing import Any

from writing_pipeline_lib import (
    asset_manifest_path,
    build_manifest_path,
    latex_escape,
    read_json,
    resolve_case_path,
    write_json,
)

LEGACY_FRAGMENT_MODE = "embedded_metadata"
METADATA_SHELL_FRAGMENT_MODE = "metadata_shell"


def clean_cell(cell: str) -> str:
    value = str(cell).strip()
    if value.startswith('="'):
        value = value[2:]
    if value.endswith('"'):
        value = value[:-1]
    value = re.sub(r'^="?|"$', "", value)
    return value.strip()


def read_esttab_csv(filepath: Path) -> tuple[list[str], list[str] | None, list[list[str]]]:
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file does not exist: {filepath}")

    with filepath.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.reader(handle))
    if len(raw_rows) < 2:
        raise ValueError(f"CSV file is too short to render as a LaTeX table: {filepath}")

    rows = [[clean_cell(cell) for cell in row] for row in raw_rows]
    plain_header = bool(
        rows
        and rows[0]
        and any(cell.strip() for cell in rows[0])
        and not any(re.match(r"\(\d+\)", cell.strip()) for cell in rows[0][1:])
    )
    if rows and rows[0] and rows[0][0].strip().lower() == "variable":
        header_index = 0
    elif plain_header:
        header_index = 0
    else:
        header_index = next(
            (
                index
                for index, row in enumerate(rows[:6])
                if [cell for cell in row[1:] if re.match(r"\(\d+\)", cell.strip())]
            ),
            1,
        )

    raw_headers = rows[header_index][1:]
    is_paired = False
    if len(raw_headers) >= 2:
        non_empty = [item for item in raw_headers if item.strip()]
        if non_empty and len(raw_headers) >= len(non_empty) * 1.5:
            is_paired = True

    if is_paired:
        headers = [""]
        for index in range(0, len(raw_headers), 2):
            header = raw_headers[index].strip() or (raw_headers[index + 1].strip() if index + 1 < len(raw_headers) else "")
            headers.append(header or f"({index // 2 + 1})")
    else:
        headers = [rows[header_index][0]] + [header or "" for header in raw_headers]

    subtitles = None
    if header_index + 1 < len(rows):
        next_row = rows[header_index + 1]
        sub_cells = [cell.strip() for cell in next_row[1:]]
        non_empty_subs = [cell for cell in sub_cells if cell and not re.match(r"^[bse]$", cell)]
        looks_like_subtitles = non_empty_subs and not any(
            cell.replace(".", "").replace("-", "").replace("*", "").isdigit()
            for cell in non_empty_subs
            if cell
        )
        if looks_like_subtitles:
            if is_paired:
                subtitles = [""]
                for index in range(0, len(sub_cells), 2):
                    subtitles.append(sub_cells[index] if index < len(sub_cells) else "")
            else:
                subtitles = [next_row[0]] + sub_cells

    data_start = header_index + 1 + (1 if subtitles else 0)
    while data_start < len(rows):
        first_cells = [cell.strip() for cell in rows[data_start][1:] if cell.strip()]
        if first_cells and all(cell in ("b", "se", "beta", "stderr") for cell in first_cells):
            data_start += 1
        else:
            break

    data_rows: list[list[str]] = []
    for row in rows[data_start:]:
        if not any(cell.strip() for cell in row):
            continue
        if is_paired:
            coef_row = [clean_cell(row[0])]
            se_row = [""]
            has_se = False
            for index in range(1, len(row), 2):
                coef = clean_cell(row[index]) if index < len(row) else ""
                stderr = clean_cell(row[index + 1]) if index + 1 < len(row) else ""
                coef_row.append(coef)
                if stderr:
                    has_se = True
                    se_row.append(stderr if stderr.startswith("(") and stderr.endswith(")") else f"({stderr})")
                else:
                    se_row.append("")
            data_rows.append(coef_row)
            if has_se and any(cell.strip() for cell in coef_row[1:]):
                data_rows.append(se_row)
        else:
            data_rows.append([clean_cell(cell) for cell in row])

    n_cols = len(headers)
    normalized_rows = [(row + [""] * max(0, n_cols - len(row)))[:n_cols] for row in data_rows]
    if subtitles:
        subtitles = (subtitles + [""] * max(0, n_cols - len(subtitles)))[:n_cols]
    return headers, subtitles, normalized_rows


def render_cell(text: str) -> str:
    stripped = text.strip()
    return latex_escape(stripped) if stripped else ""


def infer_column_spec(n_cols: int) -> str:
    if n_cols <= 1:
        return "@{}l@{}"
    return "@{}l " + " ".join(["c" for _ in range(max(1, n_cols - 1))]) + " @{}"


def split_note_lines(note: str, lang: str) -> list[str]:
    pattern = r"\n+|；" if lang == "zh" else r"\n+"
    parts = [segment.strip() for segment in re.split(pattern, note) if segment.strip()]
    return parts or ([note.strip()] if note.strip() else [])


def extract_spanner(subtitles: list[str] | None) -> tuple[str | None, list[str] | None]:
    if not subtitles or len(subtitles) <= 1:
        return None, subtitles
    unique = {item.strip() for item in subtitles[1:] if item.strip()}
    if len(unique) == 1:
        return next(iter(unique)), None
    return None, subtitles


def build_table_tex_embedded_metadata(
    title: str,
    label: str,
    headers: list[str],
    subtitles: list[str] | None,
    data_rows: list[list[str]],
    note: str,
    lang: str,
) -> str:
    n_cols = len(headers)
    col_spec = infer_column_spec(n_cols)
    col_count = max(1, n_cols)
    spanner, display_subtitles = extract_spanner(subtitles)
    continuation = "Continued Table" if lang == "en" else "续\\tablename"
    next_page = "Continued on next page" if lang == "en" else "续下页"
    continuation_head = "\\multicolumn{{{}}}{{c}}{{{{{} \\thetable{{}}\\quad {}}}}} \\\\".format(
        col_count,
        continuation,
        latex_escape(title),
    )

    lines: list[str] = ["{\\small", f"\\begin{{longtable}}{{{col_spec}}}", f"\\caption{{{latex_escape(title)}}} \\label{{{label}}} \\\\", "\\toprule"]
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    lines.append(" & ".join(render_cell(cell) for cell in headers) + r" \\")
    if display_subtitles:
        lines.append(" & ".join(render_cell(cell) for cell in display_subtitles) + r" \\")
    lines.extend(["\\midrule", "\\endfirsthead", "", continuation_head, "\\toprule"])
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    lines.append(" & ".join(render_cell(cell) for cell in headers) + r" \\")
    if display_subtitles:
        lines.append(" & ".join(render_cell(cell) for cell in display_subtitles) + r" \\")
    lines.extend(["\\midrule", "\\endhead", "", "\\midrule", f"\\multicolumn{{{col_count}}}{{r@{{}}}}{{{latex_escape(next_page)}}} \\\\", "\\endfoot", "", "\\bottomrule"])
    for note_line in split_note_lines(note, lang):
        lines.append(f"\\multicolumn{{{col_count}}}{{@{{}}p{{\\dimexpr\\linewidth-2\\tabcolsep\\relax}}}}{{\\footnotesize {latex_escape(note_line)}}} \\\\")
    lines.extend(["\\endlastfoot", ""])
    for row in data_rows:
        lines.append(" & ".join(render_cell(cell) for cell in row) + r" \\")
    lines.extend(["\\end{longtable}", "}"])
    return "\n".join(lines) + "\n"


def build_table_tex_metadata_shell(
    headers: list[str],
    subtitles: list[str] | None,
    data_rows: list[list[str]],
    lang: str,
) -> str:
    n_cols = len(headers)
    col_spec = infer_column_spec(n_cols)
    col_count = max(1, n_cols)
    spanner, display_subtitles = extract_spanner(subtitles)
    continuation = "Continued Table" if lang == "en" else "续\\tablename"
    next_page = "Continued on next page" if lang == "en" else "续下页"
    continuation_head = "\\multicolumn{{{}}}{{c}}{{{{{} \\thetable{{}}\\quad \\WritingAssetCaptionText}}}} \\\\".format(
        col_count,
        continuation,
    )

    lines: list[str] = ["{\\small", f"\\begin{{longtable}}{{{col_spec}}}", "\\UseWritingLongtableMeta", "\\toprule"]
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    lines.append(" & ".join(render_cell(cell) for cell in headers) + r" \\")
    if display_subtitles:
        lines.append(" & ".join(render_cell(cell) for cell in display_subtitles) + r" \\")
    lines.extend(["\\midrule", "\\endfirsthead", "", continuation_head, "\\toprule"])
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    lines.append(" & ".join(render_cell(cell) for cell in headers) + r" \\")
    if display_subtitles:
        lines.append(" & ".join(render_cell(cell) for cell in display_subtitles) + r" \\")
    lines.extend(
        [
            "\\midrule",
            "\\endhead",
            "",
            "\\midrule",
            f"\\multicolumn{{{col_count}}}{{r@{{}}}}{{{latex_escape(next_page)}}} \\\\",
            "\\endfoot",
            "",
            "\\bottomrule",
            f"\\UseWritingLongtableNote{{{col_count}}}",
            "\\endlastfoot",
            "",
        ]
    )
    for row in data_rows:
        lines.append(" & ".join(render_cell(cell) for cell in row) + r" \\")
    lines.extend(["\\end{longtable}", "}"])
    return "\n".join(lines) + "\n"


def build_figure_tex_embedded_metadata(title: str, label: str, figure_path: str, note: str, lang: str) -> str:
    lines = [
        "\\begin{figure}[htbp]",
        "\\centering",
        f"\\includegraphics[width=0.82\\textwidth]{{{figure_path}}}",
        f"\\caption{{{latex_escape(title)}}}",
        f"\\label{{{label}}}",
    ]
    for note_line in split_note_lines(note, lang):
        lines.append(f"\\par\\vspace{{4pt}}\\noindent\\footnotesize {latex_escape(note_line)}\\normalsize")
    lines.append("\\end{figure}")
    return "\n".join(lines) + "\n"


def build_figure_tex_metadata_shell(figure_path: str) -> str:
    lines = [
        "\\begin{figure}[htbp]",
        "\\centering",
        f"\\includegraphics[width=0.82\\textwidth]{{{figure_path}}}",
        "\\UseWritingFigureMeta",
        "\\UseWritingFigureNote",
        "\\end{figure}",
    ]
    return "\n".join(lines) + "\n"


def localize(asset: dict[str, Any], key: str, language: str, fallback: str = "") -> str:
    if language == "en":
        return str(asset.get(f"{key}_en") or asset.get(key) or fallback)
    return str(asset.get(key) or fallback)


def localize_case_path(case_root: Path, asset: dict[str, Any], key: str, language: str) -> Path | None:
    if language == "en":
        candidates = [asset.get(f"{key}_en"), asset.get(key)]
    else:
        candidates = [asset.get(f"{key}_zh"), asset.get(key)]

    for candidate in candidates:
        resolved = resolve_case_path(case_root, candidate)
        if resolved is not None:
            return resolved
    return None


def fragment_mode(asset: dict[str, Any]) -> str:
    mode = str(asset.get("fragment_mode") or LEGACY_FRAGMENT_MODE).strip().lower()
    if mode not in {LEGACY_FRAGMENT_MODE, METADATA_SHELL_FRAGMENT_MODE}:
        raise ValueError(f"Unsupported fragment_mode for asset {asset.get('asset_id')}: {mode}")
    return mode


def render_from_manifest(case_root: Path, asset_manifest_file: Path | None = None, build_manifest_file: Path | None = None) -> Path:
    asset_manifest_file = asset_manifest_file or asset_manifest_path(case_root)
    build_manifest_file = build_manifest_file or build_manifest_path(case_root)

    asset_manifest = read_json(asset_manifest_file, {"schema_version": 1, "assets": []})
    build_manifest = read_json(build_manifest_file, {})
    rendered_root = case_root / build_manifest.get("rendered_asset_dir", "outputs/build/rendered_assets")

    report: dict[str, Any] = {
        "asset_manifest": str(asset_manifest_file),
        "rendered_root": str(rendered_root),
        "rendered_assets": [],
    }

    for language in ("zh", "en"):
        (rendered_root / language / "fragments").mkdir(parents=True, exist_ok=True)
        (rendered_root / language / "figures").mkdir(parents=True, exist_ok=True)

    for asset in asset_manifest.get("assets", []):
        if asset.get("status", "draft") == "ignored":
            continue

        asset_type = asset.get("type")
        if asset_type not in {"table", "figure"}:
            continue

        asset_id = str(asset.get("asset_id") or Path(str(asset.get("source_path") or "asset")).stem)
        source_path = resolve_case_path(case_root, asset.get("source_path"))
        source_exists = source_path is not None and source_path.exists()
        mode = fragment_mode(asset)
        rendered_entry: dict[str, Any] = {
            "asset_id": asset_id,
            "type": asset_type,
            "fragment_mode": mode,
            "source_path": str(source_path) if source_path is not None else None,
            "source_exists": source_exists,
            "languages": [],
        }
        rendered_any = False

        if asset_type == "table":
            headers: list[str] | None = None
            subtitles: list[str] | None = None
            rows: list[list[str]] | None = None

            for language in ("zh", "en"):
                fragment_path = rendered_root / language / "fragments" / f"{asset_id}.tex"
                fragment_source_path = localize_case_path(case_root, asset, "fragment_source_path", language)
                if fragment_source_path is not None:
                    if not fragment_source_path.exists():
                        raise FileNotFoundError(f"Fragment source does not exist: {fragment_source_path}")
                    shutil.copy2(fragment_source_path, fragment_path)
                    rendered_entry["languages"].append(
                        {
                            "language": language,
                            "fragment_path": str(fragment_path),
                            "fragment_source_path": str(fragment_source_path),
                            "render_strategy": "copy_fragment",
                        }
                    )
                    rendered_any = True
                    continue

                if not source_exists or source_path is None:
                    continue
                if headers is None or rows is None:
                    headers, subtitles, rows = read_esttab_csv(source_path)

                title = localize(asset, "title", language, source_path.stem)
                note = localize(asset, "note", language, "")
                label = f"tab:{language}_{asset_id}"
                rendered_tex = (
                    build_table_tex_metadata_shell(headers, subtitles, rows, language)
                    if mode == METADATA_SHELL_FRAGMENT_MODE
                    else build_table_tex_embedded_metadata(title, label, headers, subtitles, rows, note, language)
                )
                fragment_path.write_text(rendered_tex, encoding="utf-8")
                rendered_entry["languages"].append(
                    {
                        "language": language,
                        "fragment_path": str(fragment_path),
                        "render_strategy": "generated_from_csv",
                    }
                )
                rendered_any = True
        else:
            for language in ("zh", "en"):
                fragment_path = rendered_root / language / "fragments" / f"{asset_id}.tex"
                fragment_source_path = localize_case_path(case_root, asset, "fragment_source_path", language)
                figure_copy_path: Path | None = None
                figure_name: str | None = None

                if source_exists and source_path is not None:
                    figure_name = f"{asset_id}{source_path.suffix.lower()}"
                    figure_copy_path = rendered_root / language / "figures" / figure_name
                    shutil.copy2(source_path, figure_copy_path)

                if fragment_source_path is not None:
                    if not fragment_source_path.exists():
                        raise FileNotFoundError(f"Fragment source does not exist: {fragment_source_path}")
                    shutil.copy2(fragment_source_path, fragment_path)
                    entry: dict[str, str] = {
                        "language": language,
                        "fragment_path": str(fragment_path),
                        "fragment_source_path": str(fragment_source_path),
                        "render_strategy": "copy_fragment",
                    }
                    if figure_copy_path is not None:
                        entry["figure_copy_path"] = str(figure_copy_path)
                    rendered_entry["languages"].append(entry)
                    rendered_any = True
                    continue

                if not source_exists or source_path is None or figure_name is None or figure_copy_path is None:
                    continue

                title = localize(asset, "title", language, source_path.stem)
                note = localize(asset, "note", language, "")
                label = f"fig:{language}_{asset_id}"
                rendered_tex = (
                    build_figure_tex_metadata_shell(f"img/generated/{figure_name}")
                    if mode == METADATA_SHELL_FRAGMENT_MODE
                    else build_figure_tex_embedded_metadata(title, label, f"img/generated/{figure_name}", note, language)
                )
                fragment_path.write_text(rendered_tex, encoding="utf-8")
                rendered_entry["languages"].append(
                    {
                        "language": language,
                        "fragment_path": str(fragment_path),
                        "figure_copy_path": str(figure_copy_path),
                        "render_strategy": "generated_from_figure",
                    }
                )
                rendered_any = True

        if rendered_any:
            report["rendered_assets"].append(rendered_entry)

    report_path = case_root / "outputs" / "runtime" / "render_assets_report.json"
    write_json(report_path, report)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render manifest-driven tables and figures into LaTeX fragments.")
    parser.add_argument("--case-root", required=True, help="Path to the writing case root.")
    parser.add_argument("--asset-manifest", help="Optional override path for the asset manifest.")
    parser.add_argument("--build-manifest", help="Optional override path for the build manifest.")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    report_path = render_from_manifest(
        case_root,
        asset_manifest_file=Path(args.asset_manifest).resolve() if args.asset_manifest else None,
        build_manifest_file=Path(args.build_manifest).resolve() if args.build_manifest else None,
    )
    print(f"Rendered asset fragments for: {case_root}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
