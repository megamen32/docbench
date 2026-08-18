from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from ..schemas import Case, Ruleset


def load_ruleset(path: Path) -> Ruleset:
    with open(path, encoding="utf-8") as f:
        return Ruleset.model_validate(yaml.safe_load(f))


def load_case(path: Path) -> Case:
    case = Case.model_validate(_load_yaml(path))
    _load_document_text_files(case, path)
    return case


def _load_document_text_files(case: Case, path: Path) -> None:
    for doc in case.documents.values():
        if not doc.text_file:
            continue
        text_path = (path.parent / doc.text_file).resolve()
        if not text_path.is_file():
            raise FileNotFoundError(f"case {case.id}: document text file not found: {text_path}")
        raw = text_path.read_bytes()
        if raw.startswith(b"\x00GITCRYPT\x00"):
            raise RuntimeError(
                f"case {case.id}: {text_path.name} is git-crypt locked; unlock the checkout first"
            )
        doc.text = raw.decode("utf-8")


def _load_yaml(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\x00GITCRYPT\x00"):
        raise RuntimeError(f"case file {path.name} is git-crypt locked; unlock the checkout first")
    return yaml.safe_load(raw.decode("utf-8"))


def load_cases(path: Path) -> list[tuple[Path, Case]]:
    files: list[Path] = []
    if path.is_file():
        files = [path]
    else:
        files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml"))
    out: list[tuple[Path, Case]] = []
    for p in files:
        raw = _load_yaml(p)
        if not isinstance(raw, dict) or "benchmark" not in raw:
            continue  # plan/registry metadata that happens to live beside cases
        case = Case.model_validate(raw)
        _load_document_text_files(case, p)
        out.append((p, case))
    return out


def ruleset_index(ruleset_dir: Path) -> dict[str, Ruleset]:
    idx: dict[str, Ruleset] = {}
    if not ruleset_dir.is_dir():
        return idx
    for p in sorted(ruleset_dir.glob("*.yaml")):
        rs = load_ruleset(p)
        idx[rs.id] = rs
    return idx


def render_docs(case: Case) -> str:
    """Human/model-readable rendering of a packet."""
    parts: list[str] = []
    for doc_id, doc in case.documents.items():
        title = f'{doc_id} (kind={doc.kind}, title={doc.title})' if doc.title else f'{doc_id} (kind={doc.kind})'
        body: dict[str, Any] = {}
        if doc.fields:
            body["fields"] = doc.fields
        if doc.table is not None:
            body["columns"] = doc.table.columns
            body["rows"] = doc.table.rows
            body["totals"] = doc.table.totals
        if doc.text:
            body["text"] = doc.text
        parts.append(f'<document id="{doc_id}" kind="{doc.kind}">\n'
                     + yaml.safe_dump(body, allow_unicode=True, sort_keys=False)
                     + "</document>")
    return "\n\n".join(parts)


class Benchmark(ABC):
    name: str

    @abstractmethod
    def messages(self, case: Case, gold: Any) -> list[dict[str, str]]: ...

    @abstractmethod
    def parse(self, text: str, case: Case) -> tuple[Any, str | None]:
        """Returns (prediction payload, parse_error)."""

    @abstractmethod
    def score(self, pred: Any, gold: Any, case: Case) -> dict[str, Any]: ...

    @abstractmethod
    def gold_for(self, case: Case) -> Any: ...
