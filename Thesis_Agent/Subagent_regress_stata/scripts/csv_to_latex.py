"""
csv_to_latex.py
读取 output/results/report_config.json，按顺序将 output/results/tables/{zh,en} 和 output/results/figures/{zh,en} 下的 CSV 表格和 PNG 图片组装成中英双语 LaTeX 报告。
输出结果：
1. output/results/latex/zh/tables/*.tex 和 output/results/latex/zh/figures/*.tex：中文片段
2. output/results/latex/en/tables/*.tex 和 output/results/latex/en/figures/*.tex：英文片段
3. output/results/latex/zh/report.tex / report_body.tex：中文主报告
4. output/results/latex/en/report.tex / report_body.tex：英文主报告
5. output/results/latex/report.tex / report.pdf：中英文合并检查版
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("REGRESSION_OUTPUT_DIR", str(ROOT / "output"))).resolve()
RESULTS_DIR = OUTPUT / "results"
CONFIG_PATH = RESULTS_DIR / "report_config.json"
LATEX_DIR = RESULTS_DIR / "latex"
ZH_DIR = LATEX_DIR / "zh"
EN_DIR = LATEX_DIR / "en"
MERGED_REPORT_TEX_PATH = LATEX_DIR / "report.tex"
ZH_TABLE_DIR = ZH_DIR / "tables"
ZH_FIGURE_DIR = ZH_DIR / "figures"
EN_TABLE_DIR = EN_DIR / "tables"
EN_FIGURE_DIR = EN_DIR / "figures"
ZH_REPORT_BODY_PATH = ZH_DIR / "report_body.tex"
EN_REPORT_BODY_PATH = EN_DIR / "report_body.tex"
ZH_REPORT_TEX_PATH = ZH_DIR / "report.tex"
EN_REPORT_TEX_PATH = EN_DIR / "report.tex"


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
        raise FileNotFoundError(f"文件不存在：{filepath}")

    with filepath.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.reader(handle))
    if len(raw_rows) < 2:
        raise ValueError(f"文件行数不足，没法生成 LaTeX 表格：{filepath}")

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


def ensure_output_dirs() -> None:
    for path in (ZH_TABLE_DIR, ZH_FIGURE_DIR, EN_TABLE_DIR, EN_FIGURE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def slugify_filename(text: str, prefix: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text.strip(), flags=re.UNICODE).strip("_")
    return cleaned or prefix


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def looks_like_numeric_cell(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    compact = stripped.replace("\n", "").replace(" ", "").replace("*", "").replace("(", "").replace(")", "").replace(",", "").replace("%", "")
    if compact.lower() in {"ref.", "ref"}:
        return False
    try:
        float(compact)
        return True
    except ValueError:
        return False


def render_inline(text: str) -> str:
    stripped = text.strip()
    return latex_escape(stripped) if stripped else ""


def render_cell(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return render_inline(stripped)


def infer_column_spec(n_cols: int) -> str:
    if n_cols <= 1:
        return "@{}l@{}"
    remaining = max(1, n_cols - 1)
    return "@{}l " + " ".join(["c" for _ in range(remaining)]) + " @{}"


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


def localize_text(item: dict[str, str], key: str, lang: str) -> str:
    if lang == "en":
        return str(item.get(f"{key}_en") or item.get(key) or "")
    return str(item.get(key) or "")


def build_table_tex(title: str, label: str, headers: list[str], subtitles: list[str] | None, data_rows: list[list[str]], note: str, lang: str) -> str:
    n_cols = len(headers)
    col_spec = infer_column_spec(n_cols)
    col_count = max(1, n_cols)
    spanner, display_subtitles = extract_spanner(subtitles)
    continuation = "Continued Table" if lang == "en" else "续\\tablename"
    next_page = "Continued on next page" if lang == "en" else "续下页"

    lines: list[str] = ["{\\small", f"\\begin{{longtable}}{{{col_spec}}}", f"\\caption{{{latex_escape(title)}}} \\label{{{label}}} \\\\", "\\toprule"]
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    header_cells = " & ".join(render_cell(cell) for cell in headers)
    lines.append(f"{header_cells} \\\\")
    if display_subtitles:
        subtitle_cells = " & ".join(render_cell(cell) for cell in display_subtitles)
        lines.append(f"{subtitle_cells} \\\\")
    lines.extend(["\\midrule", "\\endfirsthead", "", f"\\multicolumn{{{col_count}}}{{c}}{{{{{continuation} \\thetable{{}}\\quad {latex_escape(title)}}}}} \\\\", "\\toprule"])
    if spanner:
        lines.append(f"& \\multicolumn{{{col_count - 1}}}{{c}}{{{latex_escape(spanner)}}} \\\\")
        lines.append(f"\\cmidrule(lr){{2-{col_count}}}")
    lines.append(f"{header_cells} \\\\")
    if display_subtitles:
        subtitle_cells = " & ".join(render_cell(cell) for cell in display_subtitles)
        lines.append(f"{subtitle_cells} \\\\")
    lines.extend(["\\midrule", "\\endhead", "", "\\midrule", f"\\multicolumn{{{col_count}}}{{r@{{}}}}{{{latex_escape(next_page)}}} \\\\", "\\endfoot", "", "\\bottomrule"])
    for note_line in split_note_lines(note, lang):
        lines.append(f"\\multicolumn{{{col_count}}}{{@{{}}p{{\\dimexpr\\linewidth-2\\tabcolsep\\relax}}}}{{\\footnotesize {latex_escape(note_line)}}} \\\\")
    lines.extend(["\\endlastfoot", ""])
    for row in data_rows:
        row_cells = " & ".join(render_cell(cell) for cell in row)
        lines.append(f"{row_cells} \\\\")
    lines.extend(["\\end{longtable}", "}"])
    return "\n".join(lines) + "\n"


def build_figure_tex(title: str, label: str, relative_path: str, note: str, lang: str) -> str:
    note_lines = split_note_lines(note, lang)
    lines = [
        "\\begin{figure}[htbp]",
        "\\centering",
        f"\\includegraphics[width=0.82\\textwidth]{{{relative_path}}}",
        f"\\caption{{{latex_escape(title)}}}",
        f"\\label{{{label}}}",
    ]
    for note_line in note_lines:
        lines.append(f"\\par\\vspace{{4pt}}\\noindent\\footnotesize {latex_escape(note_line)}\\normalsize")
    lines.append("\\end{figure}")
    return "\n".join(lines) + "\n"


def build_report_tex(title: str, body_name: str, lang: str) -> str:
    documentclass = "article" if lang == "en" else "ctexart"
    english_caption_names = "\\renewcommand{\\tablename}{Table}\n\\renewcommand{\\figurename}{Figure}\n" if lang == "en" else ""
    return (
        f"\\documentclass[12pt]{{{documentclass}}}\n"
        "\\usepackage[a4paper,margin=2.5cm]{geometry}\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage{longtable}\n"
        "\\usepackage{multirow}\n"
        "\\usepackage{makecell}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{caption}\n"
        "\\usepackage{array}\n"
        "\\usepackage{setspace}\n"
        f"{english_caption_names}"
        "\\captionsetup[table]{skip=6pt}\n"
        "\\captionsetup[figure]{skip=6pt}\n"
        "\\pagestyle{plain}\n"
        "\\begin{document}\n"
        "\\begin{center}\n"
        f"{{\\LARGE\\bfseries {latex_escape(title)}\\par}}\n"
        "\\end{center}\n"
        "\\vspace{1em}\n"
        f"\\input{{{body_name}}}\n"
        "\\end{document}\n"
    )


def build_merged_report_tex(title_zh: str, title_en: str) -> str:
    return (
        "\\documentclass[12pt]{ctexart}\n"
        "\\usepackage[a4paper,margin=2.5cm]{geometry}\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage{longtable}\n"
        "\\usepackage{multirow}\n"
        "\\usepackage{makecell}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{caption}\n"
        "\\usepackage{array}\n"
        "\\usepackage{import}\n"
        "\\usepackage{setspace}\n"
        "\\captionsetup[table]{skip=6pt}\n"
        "\\captionsetup[figure]{skip=6pt}\n"
        "\\pagestyle{plain}\n"
        "\\begin{document}\n"
        "\\begin{center}\n"
        f"{{\\LARGE\\bfseries {latex_escape(title_zh)}\\par}}\n"
        "\\end{center}\n"
        "\\vspace{1em}\n"
        "\\renewcommand{\\tablename}{表}\n"
        "\\renewcommand{\\figurename}{图}\n"
        "\\subimport{zh/}{report_body.tex}\n"
        "\\clearpage\n"
        "\\begin{center}\n"
        f"{{\\LARGE\\bfseries {latex_escape(title_en)}\\par}}\n"
        "\\end{center}\n"
        "\\vspace{1em}\n"
        "\\renewcommand{\\tablename}{Table}\n"
        "\\renewcommand{\\figurename}{Figure}\n"
        "\\subimport{en/}{report_body.tex}\n"
        "\\end{document}\n"
    )


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def get_language_paths(lang: str) -> tuple[Path, Path, Path]:
    if lang == "en":
        return EN_TABLE_DIR, EN_FIGURE_DIR, EN_DIR
    return ZH_TABLE_DIR, ZH_FIGURE_DIR, ZH_DIR


def get_item_source_path(item: dict[str, object], lang: str) -> Path:
    language_key = f"file_{lang}"
    relative_file = item.get(language_key) or item.get("file", "")
    if not relative_file:
        raise FileNotFoundError(f"报告配置缺少 {language_key} 或 file 字段。")
    return OUTPUT / str(relative_file)


def validate_report_inputs(config: dict[str, object]) -> None:
    missing: list[str] = []
    for lang in ("zh", "en"):
        for index, item in enumerate(config.get("items", []), start=1):
            try:
                source_path = get_item_source_path(item, lang)
            except FileNotFoundError as exc:
                missing.append(f"第 {index} 项 {lang} 配置不完整: {exc}")
                continue
            if not source_path.exists():
                title = localize_text(item, "title", lang) or f"item_{index}"
                missing.append(f"第 {index} 项 {lang} 文件缺失: {title} -> {source_path}")
    if missing:
        detail = "\n".join(missing)
        raise FileNotFoundError(f"报告缺少表或图，已停止生成。\n{detail}")


def build_outputs_for_language(config: dict[str, object], lang: str) -> tuple[str, str]:
    body_chunks: list[str] = []
    table_index = 0
    figure_index = 0
    table_dir, figure_dir, language_dir = get_language_paths(lang)

    for item in config.get("items", []):
        item_type = item.get("type", "")
        item_title = localize_text(item, "title", lang)
        item_note = localize_text(item, "note", lang)
        item_description = localize_text(item, "description", lang)
        source_path = get_item_source_path(item, lang)

        if item_type == "table":
            if item_description:
                body_chunks.extend([latex_escape(item_description), ""])
            table_index += 1
            headers, subtitles, data_rows = read_esttab_csv(source_path)
            label = f"tab:{lang}_{table_index}"
            file_stem = slugify_filename(source_path.stem or item_title, f"table_{table_index}")
            target_path = table_dir / f"{file_stem}.tex"
            write_text(target_path, build_table_tex(item_title, label, headers, subtitles, data_rows, item_note, lang))
            body_chunks.extend([f"\\input{{tables/{target_path.name}}}", ""])
            print(f"  完成 {item_title}")
        elif item_type == "figure":
            if not source_path.exists():
                raise FileNotFoundError(f"图片不存在：{source_path}")
            figure_index += 1
            label = f"fig:{lang}_{figure_index}"
            file_stem = slugify_filename(source_path.stem or item_title, f"figure_{figure_index}")
            target_path = figure_dir / f"{file_stem}.tex"
            figure_relative_path = os.path.relpath(source_path, language_dir).replace("\\", "/")
            write_text(target_path, build_figure_tex(item_title, label, figure_relative_path, item_note, lang))
            body_chunks.extend([f"\\input{{figures/{target_path.name}}}", ""])
            if item_description:
                body_chunks.extend([latex_escape(item_description), ""])
            print(f"  完成 {item_title}")
        elif item_type == "page_break":
            body_chunks.extend(["\\clearpage", ""])

    body_name = "report_body.tex"
    title = str(config.get("title_en") if lang == "en" else config.get("title") or ("Regression Analysis Report" if lang == "en" else "回归分析报告"))
    return ("\n".join(body_chunks).strip() + "\n", build_report_tex(title, body_name, lang))


def summarize_latex_error(log_path: Path) -> str:
    if not log_path.exists():
        return "编译没成功，但没找到日志文件。"
    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    error_lines = [line.strip() for line in lines if line.strip().startswith("!")]
    if error_lines:
        return f"编译没成功，最主要的问题是：{error_lines[0]}"
    return "编译没成功，日志里没有抓到明确错误行，建议看 report.log。"


def compile_merged_report() -> None:
    if shutil.which("latexmk") is None:
        raise RuntimeError("当前环境没有找到 latexmk，没法生成 PDF。")
    command = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        "-file-line-error",
        "report.tex",
    ]
    result = subprocess.run(command, cwd=LATEX_DIR, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        summary = summarize_latex_error(LATEX_DIR / "report.log")
        print(f"错误 {summary}")
        raise RuntimeError(summary)
    print(f"完成 合并检查版 PDF 已生成: {LATEX_DIR / 'report.pdf'}")


def main() -> None:
    if not CONFIG_PATH.exists():
        print(f"错误 配置文件不存在: {CONFIG_PATH}")
        print("  请先创建 output/results/report_config.json")
        sys.exit(1)

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    ensure_output_dirs()
    validate_report_inputs(config)

    print("=" * 60)
    print("  生成中英双语 LaTeX 回归报告")
    print("=" * 60)

    report_body_zh, report_tex_zh = build_outputs_for_language(config, "zh")
    report_body_en, report_tex_en = build_outputs_for_language(config, "en")
    title_zh = str(config.get("title") or "回归分析报告")
    title_en = str(config.get("title_en") or "Regression Analysis Report")
    write_text(ZH_REPORT_BODY_PATH, report_body_zh)
    write_text(EN_REPORT_BODY_PATH, report_body_en)
    write_text(ZH_REPORT_TEX_PATH, report_tex_zh)
    write_text(EN_REPORT_TEX_PATH, report_tex_en)
    write_text(MERGED_REPORT_TEX_PATH, build_merged_report_tex(title_zh, title_en))
    compile_merged_report()

    print()
    print(f"完成 中文报告主文件已保存: {ZH_REPORT_TEX_PATH}")
    print(f"完成 英文报告主文件已保存: {EN_REPORT_TEX_PATH}")
    print(f"完成 合并检查版主文件已保存: {MERGED_REPORT_TEX_PATH}")
    print(f"完成 中文表格片段目录: {ZH_TABLE_DIR}")
    print(f"完成 英文表格片段目录: {EN_TABLE_DIR}")


if __name__ == "__main__":
    main()
