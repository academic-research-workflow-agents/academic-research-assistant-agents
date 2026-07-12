from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTHORING_MODE = "markdown"
VALID_AUTHORING_MODES = {"markdown", "direct_latex"}
DEFAULT_MARKDOWN_RENDERER = {
    "engine": "pandoc",
    "reader_format": "markdown+footnotes+raw_tex",
    "writer_format": "latex",
    "extra_args": ["--wrap=none", "--no-highlight"],
}
MULTI_SUFFIX_ARTIFACTS = (
    ".fdb_latexmk",
    ".run.xml",
    ".synctex.gz",
)
SIMPLE_SUFFIX_ARTIFACTS = {
    ".aux",
    ".bcf",
    ".bbl",
    ".blg",
    ".fls",
    ".log",
    ".out",
    ".toc",
    ".xdv",
}
TEMPLATE_SOURCE_CASE_ID = "thesis_template_source_case"
PRIVATE_METADATA_COMMANDS = (
    "zhtitle",
    "entitle",
    "titlelines",
    "zhauthorname",
    "enauthorname",
    "mystudentid",
    "zhmentorname",
    "enmentorname",
    "zhmajor",
    "enmajor",
    "majordirection",
    "isacademicdegree",
    "zhkeywords",
    "enkeywords",
    "theyear",
    "themonth",
)
TEMPLATE_SHELL_SKIP_DIRS = {"output", ".git"}
TEMPLATE_SHELL_CONTENT_DIRS = {"parts/en/chap", "parts/zh/chap"}
TEMPLATE_SHELL_CONTENT_FILES = {"parts/en/ref.bib", "parts/zh/ref.bib"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MarkdownRenderError(RuntimeError):
    def __init__(self, message: str, category: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.details = details or {}


def normalize_authoring_mode(value: str | None) -> str:
    mode = (value or DEFAULT_AUTHORING_MODE).strip().lower()
    if mode not in VALID_AUTHORING_MODES:
        supported = ", ".join(sorted(VALID_AUTHORING_MODES))
        raise ValueError(f"Unsupported authoring mode: {value!r}. Supported values: {supported}.")
    return mode


def default_markdown_renderer() -> dict[str, Any]:
    return {
        "engine": DEFAULT_MARKDOWN_RENDERER["engine"],
        "reader_format": DEFAULT_MARKDOWN_RENDERER["reader_format"],
        "writer_format": DEFAULT_MARKDOWN_RENDERER["writer_format"],
        "extra_args": list(DEFAULT_MARKDOWN_RENDERER["extra_args"]),
    }


def normalize_markdown_renderer(value: dict[str, Any] | None) -> dict[str, Any]:
    config = default_markdown_renderer()
    if not isinstance(value, dict):
        return config

    engine = str(value.get("engine") or config["engine"]).strip().lower()
    if engine != "pandoc":
        raise ValueError(f"Unsupported markdown renderer engine: {engine!r}. Supported value: 'pandoc'.")
    config["engine"] = engine

    reader_format = str(value.get("reader_format") or config["reader_format"]).strip()
    writer_format = str(value.get("writer_format") or config["writer_format"]).strip()
    extra_args = value.get("extra_args", config["extra_args"])
    if not isinstance(extra_args, list) or not all(isinstance(item, str) for item in extra_args):
        raise ValueError("markdown_renderer.extra_args must be a list of strings.")

    config["reader_format"] = reader_format
    config["writer_format"] = writer_format
    config["extra_args"] = list(extra_args)
    return config


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_text(path: Path, content: str, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return
    path.write_text(content, encoding="utf-8")


def relpath_from(base: Path, target: Path) -> str:
    return os.path.relpath(target, base).replace("\\", "/")


def resolve_case_path(case_root: Path, relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return candidate
    return (case_root / candidate).resolve()


def case_manifest_path(case_root: Path) -> Path:
    return case_root / "manuscript" / "manifests" / "case_manifest.json"


def asset_manifest_path(case_root: Path) -> Path:
    return case_root / "manuscript" / "manifests" / "asset_manifest.json"


def chapter_manifest_path(case_root: Path) -> Path:
    return case_root / "manuscript" / "manifests" / "chapter_manifest.json"


def build_manifest_path(case_root: Path) -> Path:
    return case_root / "manuscript" / "manifests" / "build_manifest.json"


def generated_chapter_dir(case_root: Path) -> Path:
    return case_root / "outputs" / "build" / "generated_chapters"


def rendered_asset_dir(case_root: Path) -> Path:
    return case_root / "outputs" / "build" / "rendered_assets"


def template_worktree_dir(case_root: Path) -> Path:
    return case_root / "outputs" / "build" / "my-thesis"


def default_template_asset_rel(case_root: Path) -> str:
    if case_root.name == TEMPLATE_SOURCE_CASE_ID:
        return "assets/my-thesis"
    return f"../{TEMPLATE_SOURCE_CASE_ID}/assets/my-thesis"


def sync_case_bibliography(case_root: Path, worktree: Path) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    for language in ("zh", "en"):
        source = bibliography_source_for_language(case_root, language)
        if not source.exists():
            continue
        destination = worktree / "parts" / language / "ref.bib"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(
            {
                "language": language,
                "source_path": str(source),
                "destination_path": str(destination),
            }
        )
    return copied


def is_compile_artifact(path: Path) -> bool:
    lowered = path.name.lower()
    if lowered == ".ds_store":
        return True
    if path.name == "main.pdf":
        return True
    if any(lowered.endswith(suffix) for suffix in MULTI_SUFFIX_ARTIFACTS):
        return True
    return path.suffix.lower() in SIMPLE_SUFFIX_ARTIFACTS


def template_ignore_names(_: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        candidate = Path(name)
        lowered = name.lower()
        if lowered == ".ds_store":
            ignored.add(name)
            continue
        if name == "output":
            ignored.add(name)
            continue
        if name == ".git":
            ignored.add(name)
            continue
        if is_compile_artifact(candidate):
            ignored.add(name)
    return ignored


def _remove_readonly(func: Any, path: str, _: Any) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def copy_template_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination, onerror=_remove_readonly)
    shutil.copytree(source, destination, ignore=template_ignore_names)


def copy_template_shell_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination, onerror=_remove_readonly)
    destination.mkdir(parents=True, exist_ok=True)

    for root, dirnames, filenames in os.walk(source):
        root_path = Path(root)
        rel_root = Path(".") if root_path == source else root_path.relative_to(source)
        rel_root_str = "" if rel_root == Path(".") else rel_root.as_posix()

        kept_dirnames: list[str] = []
        for dirname in dirnames:
            candidate_rel = f"{rel_root_str}/{dirname}" if rel_root_str else dirname
            if dirname in TEMPLATE_SHELL_SKIP_DIRS:
                continue
            if candidate_rel in TEMPLATE_SHELL_CONTENT_DIRS:
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        destination_root = destination if rel_root == Path(".") else destination / rel_root
        destination_root.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            candidate_rel = f"{rel_root_str}/{filename}" if rel_root_str else filename
            if candidate_rel in TEMPLATE_SHELL_CONTENT_FILES:
                continue
            if is_compile_artifact(Path(filename)):
                continue
            shutil.copy2(root_path / filename, destination_root / filename)

    for rel_dir in sorted(TEMPLATE_SHELL_CONTENT_DIRS):
        (destination / Path(rel_dir)).mkdir(parents=True, exist_ok=True)


def chapter_blueprint(mode: str) -> list[dict[str, Any]]:
    ext = ".md" if mode == "markdown" else ".tex"
    entries: list[dict[str, Any]] = [
        {
            "id": "abstract",
            "order": 10,
            "kind": "abstract",
            "zh_source": f"manuscript/zh/abstract{ext}",
            "en_source": f"manuscript/en/abstract{ext}",
            "zh_target": "parts/zh/chap/abstract.tex",
            "en_target": "parts/en/chap/abstract.tex",
            "upstream_refs": [],
            "notes": "Bilingual abstract entrypoint."
        }
    ]
    for order, chapter_id in enumerate(("chap1", "chap2", "chap3", "chap4", "chap5", "chap6"), start=20):
        entries.append(
            {
                "id": chapter_id,
                "order": order,
                "kind": "chapter",
                "zh_source": f"manuscript/zh/{chapter_id}{ext}",
                "en_source": f"manuscript/en/{chapter_id}{ext}",
                "zh_target": f"parts/zh/chap/{chapter_id}.tex",
                "en_target": f"parts/en/chap/{chapter_id}.tex",
                "upstream_refs": [],
                "notes": ""
            }
        )
    entries.append(
        {
            "id": "acknowledgement",
            "order": 80,
            "kind": "acknowledgement",
            "zh_source": f"manuscript/zh/acknowledgement{ext}",
            "en_source": None,
            "zh_target": "parts/zh/chap/acknowledgement.tex",
            "en_target": None,
            "upstream_refs": [],
            "notes": "Chinese-only acknowledgement chapter."
        }
    )
    return entries


def default_case_manifest(case_root: Path, mode: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_root.name,
        "case_title": f"{case_root.name} writing case",
        "description": "Initialized writing case. Replace the generic planning text as the case converges on real manuscript work.",
        "authoring_mode": mode,
        "markdown_renderer": default_markdown_renderer(),
        "languages": ["zh", "en"],
        "upstream_sources": [],
        "template": {
            "asset_path": default_template_asset_rel(case_root),
            "worktree_path": "outputs/build/my-thesis"
        },
        "manifests": {
            "chapter_manifest": "manuscript/manifests/chapter_manifest.json",
            "asset_manifest": "manuscript/manifests/asset_manifest.json",
            "build_manifest": "manuscript/manifests/build_manifest.json"
        },
        "output_policy": {
            "build_dir": "outputs/build",
            "preview_dir": "outputs/preview",
            "runtime_dir": "outputs/runtime"
        }
    }


def default_asset_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "assets": []
    }


def default_chapter_manifest(mode: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authoring_mode": mode,
        "chapters": chapter_blueprint(mode)
    }


def default_build_manifest(case_root: Path, mode: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authoring_mode": mode,
        "template_asset_path": default_template_asset_rel(case_root),
        "template_worktree_path": "outputs/build/my-thesis",
        "generated_chapter_dir": "outputs/build/generated_chapters",
        "rendered_asset_dir": "outputs/build/rendered_assets",
        "last_scan_report": None,
        "last_materialized_at": None,
        "last_injected_at": None,
        "last_compiled_at": None,
        "last_compile_stage": None,
        "status": "not_started",
        "compiled_outputs": []
    }


def chapter_placeholder(chapter_id: str, kind: str, language: str, mode: str) -> str:
    if mode == "direct_latex":
        if kind == "abstract":
            if language == "zh":
                return "\\begin{cabstract}\n\t\\addcontentsline{toc}{chapter}{摘要}\n\n待补写中文摘要。\n\\end{cabstract}\n"
            return "\\begin{eabstract}\n\t\\addcontentsline{toc}{chapter}{ABSTRACT}\n\nEnglish abstract placeholder.\n\\end{eabstract}\n"
        if kind == "acknowledgement":
            return "\\chapter{致谢}\n\n待补写致谢内容。\n"
        title = "占位标题" if language == "zh" else "Placeholder Title"
        return f"\\chapter{{{title}}}\n\n{'待补写。' if language == 'zh' else 'Draft content goes here.'}\n"

    if kind == "abstract":
        return "待补写中文摘要。\n" if language == "zh" else "English abstract placeholder.\n"
    if kind == "acknowledgement":
        return "# 致谢\n\n待补写致谢内容。\n"
    heading = "# 占位标题\n\n" if language == "zh" else "# Placeholder Title\n\n"
    body = "待补写。\n" if language == "zh" else "Draft content goes here.\n"
    return heading + body


def ensure_case_skeleton(case_root: Path, mode: str) -> None:
    directories = (
        case_root / "assets",
        case_root / "requests",
        case_root / "scripts",
        case_root / "skills",
        case_root / "manuscript" / "manifests",
        case_root / "manuscript" / "zh",
        case_root / "manuscript" / "en",
        case_root / "outputs" / "build",
        case_root / "outputs" / "preview",
        case_root / "outputs" / "runtime",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def default_case_agents(case_name: str) -> str:
    return f"""# {case_name}

## Role
This is a generic writing case initialized from the writing layer defaults.

Use it to:
- bind upstream research cases
- edit bilingual manuscript sources
- generate chapter `.tex`
- build a case-local LaTeX worktree

Do not use this case to:
- rerun upstream cleaning
- redefine regression specifications by default
- treat generic initialization text as final research content

## Case Contract
- keep manuscript sources under `manuscript/`
- keep case-local personal skills under `skills/`
- keep manifests under `manuscript/manifests/`
- keep generated LaTeX and template worktree outputs under `outputs/build/`
- keep preview PDFs under `outputs/preview/`
- keep scan/build reports under `outputs/runtime/`

## Markdown Authoring Rules
- standard footnotes such as `[^note]` are allowed in `markdown` mode
- raw LaTeX such as `\\footnote{{}}`, `\\cite{{}}`, and `\\begin{{...}}` is allowed in manuscript body text
- for chapter-like files, keep the first `# ` line as the chapter title
- for chapter-like files, start body headings from `##`
"""


def default_case_readme(case_name: str, mode: str) -> str:
    if mode == "direct_latex":
        return f"""# {case_name}

这是初始化后的写作层通用 case。

## 当前模式
- `authoring_mode = direct_latex`

## Direct LaTeX 工作约定
- 当前稿源直接维护在 `manuscript/zh/*.tex` 与 `manuscript/en/*.tex`
- 优先直接修改 `.tex` 正文，再按需运行生成与构建脚本
- case-local personal skills 保留在 `skills/`，风格补充放在 `references/style-profile.md`

## 这是干什么的
- 绑定一个或多个上游 research case
- 维护 case-local personal skills
- 维护中英双语 LaTeX 稿件源文件
- 生成可注入 `my-thesis` 模板的章节和表图片段

## 下一步通常怎么继续
1. 在 `manuscript/manifests/case_manifest.json` 中登记 upstream case。
2. 直接编辑 `manuscript/zh/` 与 `manuscript/en/` 下的 `.tex` 文件。
3. 需要刷新章节生成物时，运行 `materialize_chapters.py`。
4. 需要刷新表图或模板工作副本时，再运行 `render_assets.py`、`inject_template.py`。
5. 需要新的预览 PDF 时，再运行 `compile_thesis.py`。
"""

    return f"""# {case_name}

这是初始化后的写作层通用 case。

## 当前模式
- `authoring_mode = {mode}`

## Markdown 写作约定
- 标准脚注可直接写成 `[^note]` 与对应脚注定义
- 正文里允许直接写 `\\footnote{{}}`、`\\cite{{}}`、`\\label{{}}`、LaTeX 环境块
- 章节型文件第一行 `# 标题` 保留给 chapter title
- 章节正文里的小节请从 `##` 开始

## 这是干什么的
- 绑定一个或多个上游 research case
- 维护 case-local personal skills
- 维护中英双语稿件源文件
- 生成可注入 `my-thesis` 模板的章节和表图片段

## 下一步通常怎么继续
1. 在 `manuscript/manifests/case_manifest.json` 中登记 upstream case。
2. 运行 `scan_upstream_sources.py` 生成扫描报告。
3. 编辑 `manuscript/zh/` 与 `manuscript/en/` 下的稿件。
4. 运行 `materialize_chapters.py`、`render_assets.py`、`inject_template.py`。
5. 需要时再运行 `compile_thesis.py`。
"""


def load_case_manifests(case_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    case_manifest = read_json(case_manifest_path(case_root), {})
    chapter_manifest = read_json(chapter_manifest_path(case_root), {})
    asset_manifest = read_json(asset_manifest_path(case_root), {})
    build_manifest = read_json(build_manifest_path(case_root), {})
    return case_manifest, chapter_manifest, asset_manifest, build_manifest


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


def extract_leading_h1(text: str) -> tuple[str | None, list[str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip(), lines[index + 1 :]
        return None, lines
    return None, lines


def replace_asset_tokens(text: str, language: str) -> str:
    pattern = re.compile(r"\{\{asset:([a-zA-Z0-9_.-]+)\}\}")

    def repl(match: re.Match[str]) -> str:
        asset_id = match.group(1)
        if language == "zh":
            return rf"\input{{../generated_assets/{asset_id}.tex}}"
        return rf"\input{{../generated_assets/{asset_id}.tex}}"

    return pattern.sub(repl, text)


def validate_markdown_heading_structure(body_text: str, kind: str) -> dict[str, Any]:
    validation = {
        "checked": kind in {"chapter", "acknowledgement"},
        "rule": "chapter_body_headings_must_start_from_h2",
        "valid": True,
        "violations": [],
    }
    if not validation["checked"]:
        return validation

    in_fenced_code = False
    violations: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(body_text.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fenced_code = not in_fenced_code
            continue
        if in_fenced_code:
            continue
        if stripped.startswith("# "):
            violations.append({"line": line_number, "text": stripped})

    validation["violations"] = violations
    validation["valid"] = len(violations) == 0
    return validation


def clean_pandoc_latex_output(text: str) -> str:
    cleaned_lines = [line for line in text.splitlines() if line.strip() != r"\tightlist"]
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\\begin\{verbatim\}", r"\\begin{Verbatim}", cleaned)
    cleaned = re.sub(r"\\end\{verbatim\}", r"\\end{Verbatim}", cleaned)
    return cleaned.strip() + "\n"


def render_markdown_body_with_pandoc(
    body_text: str,
    renderer: dict[str, Any] | None,
    heading_shift: int | None,
) -> dict[str, Any]:
    config = normalize_markdown_renderer(renderer)
    pandoc_path = shutil.which("pandoc")
    if pandoc_path is None:
        raise MarkdownRenderError(
            "Pandoc is required for markdown mode. Install Pandoc or switch this case to direct_latex.",
            "missing_pandoc",
            {"engine": config["engine"]},
        )

    command = [
        pandoc_path,
        "--from",
        config["reader_format"],
        "--to",
        config["writer_format"],
        *config["extra_args"],
    ]
    if heading_shift is not None and heading_shift != 0:
        command.append(f"--shift-heading-level-by={heading_shift}")

    result = subprocess.run(
        command,
        input=body_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    warnings = [line.strip() for line in (result.stderr or "").splitlines() if line.strip()]
    if result.returncode != 0:
        raise MarkdownRenderError(
            "Pandoc failed to convert the markdown manuscript body.",
            "pandoc_failed",
            {
                "command": subprocess.list2cmdline(command),
                "warnings": warnings,
                "returncode": result.returncode,
            },
        )

    try:
        rendered = clean_pandoc_latex_output(result.stdout or "")
    except Exception as exc:
        raise MarkdownRenderError(
            "Pandoc conversion succeeded, but LaTeX post-processing failed.",
            "pandoc_postprocess_failed",
            {
                "command": subprocess.list2cmdline(command),
                "warnings": warnings,
                "reason": str(exc),
            },
        ) from exc

    return {
        "rendered_body": rendered,
        "renderer": config,
        "pandoc_command": subprocess.list2cmdline(command),
        "warnings": warnings,
    }


def render_markdown_document(
    text: str,
    language: str,
    kind: str,
    renderer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title, body_lines = extract_leading_h1(text)
    body = "\n".join(body_lines).strip()
    heading_validation = validate_markdown_heading_structure(body, kind)
    if heading_validation["checked"] and not heading_validation["valid"]:
        raise MarkdownRenderError(
            "Markdown heading validation failed: chapter-like files must keep only the first '# ' as the chapter title, and body headings must start from '##'.",
            "invalid_heading_structure",
            {"heading_validation": heading_validation},
        )

    body = replace_asset_tokens(body, language)
    heading_shift = -1 if kind in {"chapter", "acknowledgement"} else None
    render_result = render_markdown_body_with_pandoc(body, renderer, heading_shift)
    latex_body = render_result["rendered_body"]

    if kind == "abstract":
        if language == "zh":
            rendered_document = (
                "\\begin{cabstract}\n"
                "\t\\addcontentsline{toc}{chapter}{摘要}\n\n"
                f"{latex_body}"
                "\\end{cabstract}\n"
            )
        else:
            rendered_document = (
                "\\begin{eabstract}\n"
                "\t\\addcontentsline{toc}{chapter}{ABSTRACT}\n\n"
                f"{latex_body}"
                "\\end{eabstract}\n"
            )
    elif kind == "acknowledgement":
        chapter_title = title or ("致谢" if language == "zh" else "Acknowledgement")
        rendered_document = f"\\chapter{{{latex_escape(chapter_title)}}}\n\n{latex_body}"
    else:
        chapter_title = title or ("占位标题" if language == "zh" else "Placeholder Title")
        rendered_document = f"\\chapter{{{latex_escape(chapter_title)}}}\n\n{latex_body}"

    return {
        "rendered": rendered_document,
        "renderer": render_result["renderer"],
        "pandoc_command": render_result["pandoc_command"],
        "warnings": render_result["warnings"],
        "heading_validation": heading_validation,
    }


def markdown_to_latex_document(text: str, language: str, kind: str, renderer: dict[str, Any] | None = None) -> str:
    return render_markdown_document(text, language, kind, renderer)["rendered"]


def cover_config_asset_path(case_root: Path) -> Path:
    return case_root / "assets" / "cover" / "configs.tex"


def bibliography_asset_path(case_root: Path, name: str) -> Path:
    return case_root / "assets" / name


def bibliography_source_for_language(case_root: Path, language: str) -> Path:
    asset_root = case_root / "assets"
    default_source = asset_root / "ref.bib"
    source = asset_root / f"ref_{language}.bib"
    if not source.exists():
        source = default_source
    return source


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _command_name_from_line(line: str) -> str | None:
    stripped = line.strip()
    for command in PRIVATE_METADATA_COMMANDS:
        if stripped.startswith(f"\\newcommand{{\\{command}}}"):
            return command
    return None


def _extract_metadata_command_lines(text: str) -> dict[str, str]:
    command_lines: dict[str, str] = {}
    for line in text.splitlines():
        command = _command_name_from_line(line)
        if command is not None:
            command_lines[command] = line
    return command_lines


def build_private_config_text(public_base_text: str, private_metadata_text: str) -> tuple[str, list[str], list[str]]:
    metadata_lines = _extract_metadata_command_lines(private_metadata_text)
    base_lines = public_base_text.splitlines()
    rewritten_commands: list[str] = []
    output_lines: list[str] = []

    for line in base_lines:
        command = _command_name_from_line(line)
        if command is not None and command in metadata_lines:
            output_lines.append(metadata_lines[command])
            rewritten_commands.append(command)
        else:
            output_lines.append(line)

    missing_commands = [command for command in PRIVATE_METADATA_COMMANDS if command not in metadata_lines]
    return "\n".join(output_lines) + "\n", rewritten_commands, missing_commands


def materialize_private_config(
    public_base_path: Path,
    private_metadata_path: Path,
    destination_path: Path,
) -> dict[str, Any]:
    public_base_text = public_base_path.read_text(encoding="utf-8")
    private_metadata_text = private_metadata_path.read_text(encoding="utf-8")
    rendered_text, rewritten_commands, missing_commands = build_private_config_text(public_base_text, private_metadata_text)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(rendered_text, encoding="utf-8")
    return {
        "public_base_path": str(public_base_path),
        "private_metadata_path": str(private_metadata_path),
        "destination_path": str(destination_path),
        "rewritten_commands": rewritten_commands,
        "missing_commands": missing_commands,
        "destination_sha256": file_sha256(destination_path),
    }


def build_private_content_source_map(
    case_root: Path,
    template_asset_path: Path,
    worktree: Path,
    chapter_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    generated_root = generated_chapter_dir(case_root)
    entries: list[dict[str, Any]] = []
    for chapter in chapter_manifest.get("chapters", []):
        if not isinstance(chapter, dict):
            continue
        chapter_id = str(chapter.get("id") or "")
        for language in ("zh", "en"):
            target_rel = chapter.get(f"{language}_target")
            if not target_rel:
                continue
            target_rel_str = str(target_rel)
            target_path = worktree / target_rel_str
            private_source = generated_root / language / Path(target_rel_str).name
            public_source = template_asset_path / target_rel_str
            actual_exists = target_path.exists()
            private_exists = private_source.exists()
            public_exists = public_source.exists()
            status = "missing"
            if actual_exists and private_exists and file_sha256(target_path) == file_sha256(private_source):
                status = "matched_private"
            elif actual_exists and public_exists and file_sha256(target_path) == file_sha256(public_source):
                status = "leaked_public"
            elif actual_exists and private_exists:
                status = "unknown"
            elif private_exists:
                status = "missing_worktree_target"
            elif actual_exists:
                status = "missing_private_source"
            entries.append(
                {
                    "entry_id": chapter_id,
                    "language": language,
                    "kind": chapter.get("kind"),
                    "target_path": str(target_path),
                    "private_source_path": str(private_source),
                    "public_source_path": str(public_source),
                    "target_exists": actual_exists,
                    "private_source_exists": private_exists,
                    "public_source_exists": public_exists,
                    "status": status,
                }
            )

    for language in ("zh", "en"):
        target_path = worktree / "parts" / language / "ref.bib"
        private_source = bibliography_source_for_language(case_root, language)
        public_source = template_asset_path / "parts" / language / "ref.bib"
        actual_exists = target_path.exists()
        private_exists = private_source.exists()
        public_exists = public_source.exists()
        status = "missing"
        if actual_exists and private_exists and file_sha256(target_path) == file_sha256(private_source):
            status = "matched_private"
        elif actual_exists and public_exists and file_sha256(target_path) == file_sha256(public_source):
            status = "leaked_public"
        elif actual_exists and private_exists:
            status = "unknown"
        elif private_exists:
            status = "missing_worktree_target"
        elif actual_exists:
            status = "missing_private_source"
        entries.append(
            {
                "entry_id": f"{language}_bibliography",
                "language": language,
                "kind": "bibliography",
                "target_path": str(target_path),
                "private_source_path": str(private_source),
                "public_source_path": str(public_source),
                "target_exists": actual_exists,
                "private_source_exists": private_exists,
                "public_source_exists": public_exists,
                "status": status,
            }
        )
    return entries


def extract_cited_keys(text: str) -> list[str]:
    pattern = re.compile(
        r"\\(?:cite|parencite|textcite|footcite|autocite|citeauthor|citeyear|supercite)"
        r"\*?(?:\[[^\]]*\])?(?:\[[^\]]*\])?\{([^}]*)\}"
    )
    cited_keys: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        for key in (item.strip() for item in match.group(1).split(",")):
            if key and key not in seen:
                seen.add(key)
                cited_keys.append(key)
    return cited_keys


def parse_bib_keys(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    start_pattern = re.compile(r"@[\w-]+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
    for match in start_pattern.finditer(text):
        key = match.group(1).strip()
        brace_index = text.find("{", match.start())
        if brace_index < 0:
            continue
        depth = 0
        end_index = None
        for index in range(brace_index, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_index = index + 1
                    break
        if end_index is None:
            continue
        entries[key] = text[match.start() : end_index].strip() + "\n"
    return entries
