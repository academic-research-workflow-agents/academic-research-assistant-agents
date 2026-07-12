from __future__ import annotations

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUBAGENT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SUBAGENT_ROOT.parent
VALID_INGEST_MODES = {"linked_bib", "manual_pdf", "mixed"}
DEFAULT_LANGUAGE = "zh"
INFO_ITEM_ALIASES = {
    "controls": ["controls", "control variable", "control variables", "控制变量", "控制", "covariates"],
    "identification": ["identification", "identification strategy", "research design", "识别策略", "识别", "研究设计", "方法"],
    "mechanism": ["mechanism", "mechanisms", "机制", "机制变量", "传导机制"],
    "endogeneity": ["endogeneity", "内生性", "内生性处理", "identification threat"],
    "sample": ["sample", "数据与样本", "样本", "数据"],
    "outcome": ["outcome", "被解释变量", "因变量", "结果变量"],
    "theme": ["theme", "themes", "topic", "topics", "主题", "文献主题", "topic grouping"],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
    try:
        return os.path.relpath(target, base).replace("\\", "/")
    except ValueError:
        return str(target)


def resolve_case_path(case_root: Path, relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return candidate
    return (case_root / candidate).resolve()


def normalize_ingest_mode(value: str | None) -> str:
    mode = (value or "").strip().lower()
    if not mode:
        raise ValueError("ingest_mode must be provided or derived before normalization.")
    if mode not in VALID_INGEST_MODES:
        supported = ", ".join(sorted(VALID_INGEST_MODES))
        raise ValueError(f"Unsupported ingest mode: {value!r}. Supported values: {supported}.")
    return mode


def detect_default_ingest_mode(workspace_root: Path | None = None) -> str:
    root = workspace_root or WORKSPACE_ROOT
    if (root / "ref.bib").exists():
        return "linked_bib"
    return "manual_pdf"


def case_manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "case_manifest.json"


def paper_manifest_path(case_root: Path) -> Path:
    return case_root / "manifests" / "paper_manifest.json"


def paper_manifest_local_path(case_root: Path) -> Path:
    return case_root / "manifests" / "paper_manifest.private.json"


def query_manifest_path(case_root: Path, query_id: str) -> Path:
    return case_root / "manifests" / "queries" / f"{query_id}.json"


def evidence_ledger_path(case_root: Path) -> Path:
    return case_root / "outputs" / "evidence" / "evidence_ledger.jsonl"


def ensure_case_skeleton(case_root: Path) -> None:
    directories = (
        case_root / "inputs" / "papers",
        case_root / "inputs" / "ref",
        case_root / "cards",
        case_root / "manifests" / "queries",
        case_root / "requests",
        case_root / "outputs" / "evidence",
        case_root / "outputs" / "queries",
        case_root / "outputs" / "runtime",
        case_root / "scripts",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def default_case_manifest(case_root: Path, ingest_mode: str, ref_bib_path: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_root.name,
        "ingest_mode": ingest_mode,
        "default_language": DEFAULT_LANGUAGE,
        "ref_bib_path": ref_bib_path,
        "paper_input_root": "inputs/papers",
        "parallel_policy": {
            "mode": "sequential",
            "allow_worker_delegation": True,
        },
        "output_policy": {
            "evidence_dir": "outputs/evidence",
            "queries_dir": "outputs/queries",
            "runtime_dir": "outputs/runtime",
        },
    }


def default_paper_manifest(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_root.name,
        "papers": [],
        "updated_at": utc_now_iso(),
    }


def default_paper_manifest_local(case_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": case_root.name,
        "papers": [],
        "updated_at": utc_now_iso(),
    }


def default_case_agents(case_name: str) -> str:
    return f"""# {case_name}

## Role
This is a reading-layer case scaffold.

Use it to:
- resolve paper inputs
- build paper manifests
- read one paper at a time into cards
- maintain the evidence ledger
- answer focused literature questions

Do not use this case to:
- draft the final literature review prose by default
- mutate linked PDFs
- leak local attachment paths into shared artifacts

## Case Contract
- keep private PDFs under `inputs/`
- keep shared manifests under `manifests/`
- keep cards under `cards/`
- keep evidence under `outputs/evidence/`
- keep query deliverables under `outputs/queries/`
"""


def default_case_readme(case_name: str, ingest_mode: str, ref_bib_path: str) -> str:
    return f"""# {case_name}

这是 reading case 骨架。

## 当前 ingest_mode
- `{ingest_mode}`

## 当前 ref_bib_path
- `{ref_bib_path}`

## 下一步通常怎么做
1. 运行 `build_paper_manifest.py`，解析 `ref.bib` 或扫描 `inputs/papers/`。
2. 对单篇论文调用 `paper-read`，生成 `cards/<citation_key>.md`。
3. 把证据条目写入 `outputs/evidence/evidence_ledger.jsonl`。
4. 运行 `run_query_summary.py` 汇总某个信息条目，并生成 `ref_v2.bib`。
"""


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "paper"


def safe_output_stem(value: str, max_length: int = 80) -> str:
    stem = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "_", value).strip("_")
    stem = re.sub(r"_+", "_", stem)
    if not stem:
        stem = "paper"
    if len(stem) <= max_length:
        return stem
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    keep = max_length - len(digest) - 1
    return f"{stem[:keep].rstrip('_')}_{digest}"


def make_manual_citation_key(stem: str, existing_keys: set[str]) -> str:
    base = f"manual-{slugify(stem)}"
    candidate = base
    index = 2
    while candidate in existing_keys:
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def extract_bib_entry_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    cursor = 0
    while True:
        start = text.find("@", cursor)
        if start == -1:
            break
        brace_start = text.find("{", start)
        if brace_start == -1:
            break
        depth = 0
        end = None
        for index in range(brace_start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end is None:
            break
        blocks.append(text[start : end + 1].strip())
        cursor = end + 1
    return blocks


def split_top_level_csv(text: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    brace_depth = 0
    in_quotes = False
    escaped = False
    for char in text:
        if char == '"' and not escaped:
            in_quotes = not in_quotes
        if char == "{" and not in_quotes:
            brace_depth += 1
        elif char == "}" and not in_quotes and brace_depth > 0:
            brace_depth -= 1
        if char == "," and brace_depth == 0 and not in_quotes:
            item_text = "".join(current).strip()
            if item_text:
                tokens.append(item_text)
            current = []
        else:
            current.append(char)
        escaped = (char == "\\" and not escaped)
        if char != "\\":
            escaped = False
    item_text = "".join(current).strip()
    if item_text:
        tokens.append(item_text)
    return tokens


def unwrap_bib_value(value: str) -> str:
    stripped = value.strip().rstrip(",")
    if len(stripped) >= 2 and stripped[0] == "{" and stripped[-1] == "}":
        return stripped[1:-1].strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        return stripped[1:-1].strip()
    return stripped


def parse_bib_entry(block: str) -> dict[str, Any]:
    match = re.match(r"^@(?P<entry_type>[A-Za-z]+)\s*\{\s*(?P<key>[^,]+)\s*,(?P<body>.*)\}\s*$", block, re.DOTALL)
    if not match:
        raise ValueError("Unable to parse BibTeX entry header.")
    body = match.group("body").strip()
    fields: dict[str, str] = {}
    for token in split_top_level_csv(body):
        if "=" not in token:
            continue
        name, raw_value = token.split("=", 1)
        fields[name.strip().lower()] = unwrap_bib_value(raw_value)
    return {
        "entry_type": match.group("entry_type").lower(),
        "citation_key": match.group("key").strip(),
        "fields": fields,
        "raw": block.strip() + "\n",
    }


def load_bib_entries(bib_path: Path) -> list[dict[str, Any]]:
    if not bib_path.exists():
        return []
    text = bib_path.read_text(encoding="utf-8")
    return [parse_bib_entry(block) for block in extract_bib_entry_blocks(text)]


def normalize_attachment_path(value: str) -> str:
    normalized = value.strip()
    normalized = normalized.replace("\\\\", "\\")
    normalized = normalized.replace("\\:", ":")
    return normalized


def extract_pdf_attachments(file_field: str | None) -> list[str]:
    if not file_field:
        return []
    attachments: list[str] = []
    for part in file_field.split(";"):
        candidate = normalize_attachment_path(part)
        if candidate.lower().endswith(".pdf"):
            attachments.append(candidate)
    return attachments


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def normalize_text_key(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[\s_\-]+", "", lowered)
    return lowered


def normalize_info_tags(info_item: str) -> list[str]:
    normalized_item = normalize_text_key(info_item)
    tags: list[str] = []
    for canonical, aliases in INFO_ITEM_ALIASES.items():
        alias_tokens = {normalize_text_key(alias) for alias in aliases}
        if normalized_item in alias_tokens or any(alias in normalized_item for alias in alias_tokens if alias):
            tags.append(canonical)
    if not tags:
        tags.append(slugify(info_item))
    return sorted(set(tags))


def filter_bib_entries(source_bib: Path | None, selected_keys: list[str], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source_bib is None or not source_bib.exists():
        destination.write_text(
            "% No source BibTeX file was available. Add bibliographic metadata before relying on this subset.\n",
            encoding="utf-8",
        )
        return
    keys = set(selected_keys)
    kept_entries = [entry["raw"] for entry in load_bib_entries(source_bib) if entry["citation_key"] in keys]
    if kept_entries:
        destination.write_text("\n".join(entry.rstrip() for entry in kept_entries).strip() + "\n", encoding="utf-8")
        return
    destination.write_text("% No BibTeX entries matched the selected citation keys.\n", encoding="utf-8")
