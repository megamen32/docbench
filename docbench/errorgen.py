"""Sidecar: deterministic controlled corruption of valid packets.

errorgen only mutates packets; gold findings are always recomputed by the
oracle at load time, so injected defects and expected findings can never
drift apart. Plans are explicit YAML (versionable, reproducible).
"""
from __future__ import annotations

import copy
import datetime as _dt
import fnmatch
import random
from pathlib import Path
from typing import Any

import yaml

from .oracle import flatten_case
from .schemas import Case


def _split_path(path: str) -> tuple[str, list[str]]:
    parts = path.split(".")
    return parts[0], parts[1:]


def mutate_field(case: Case, path: str, value: Any) -> bool:
    """Set a value addressed in flat space: doc.field, doc.totals.key,
    doc.row.<category>.<column>, documents.<doc>.present is read-only."""
    doc_id, rest = _split_path(path)
    doc = case.documents.get(doc_id)
    if doc is None:
        return False
    if not rest:
        return False
    if rest == ["text"]:
        doc.text = str(value)
        return True
    if len(rest) >= 2 and rest[0] == "totals":
        if doc.table is None:
            return False
        doc.table.totals[".".join(rest[1:])] = value
        return True
    if len(rest) >= 3 and rest[0] == "row":
        if doc.table is None:
            return False
        cat, col = rest[1], ".".join(rest[2:])
        for row in doc.table.rows:
            if str(row.get("category")) == cat:
                row[col] = value
                return True
        return False
    if len(rest) == 1:
        doc.fields[rest[0]] = value
        return True
    # nested plain dicts inside fields
    cur = doc.fields
    for p in rest[:-1]:
        if not isinstance(cur.get(p), dict):
            return False
        cur = cur[p]
    cur[rest[-1]] = value
    return True


def read_field(case: Case, path: str) -> Any:
    return flatten_case(case).get(path)


def resolve_glob(case: Case, pattern: str) -> list[str]:
    return [k for k in flatten_case(case) if fnmatch.fnmatch(k, pattern)]


def _resolve_value(case: Case, spec: Any) -> Any:
    if isinstance(spec, dict) and "copy_from" in spec:
        base = read_field(case, spec["copy_from"])
        delta = spec.get("delta", 0)
        if isinstance(base, (int, float)) and not isinstance(base, bool):
            return type(base)(base + delta)
        if isinstance(base, str):
            try:
                d = _dt.date.fromisoformat(base)
                return (d + _dt.timedelta(days=delta)).isoformat()
            except ValueError:
                return base
        return base
    return spec


OPS: dict[str, Any] = {}


def op(name):
    def deco(fn):
        OPS[name] = fn
        return fn
    return deco


@op("remove_document")
def remove_document(case: Case, rng: random.Random, params: dict) -> str:
    doc_id = params.get("doc_id")
    if doc_id is None:
        doc_id = rng.choice(sorted(case.documents))
    if doc_id not in case.documents:
        raise KeyError(f"remove_document: no document {doc_id!r}")
    title = case.documents[doc_id].title or doc_id
    del case.documents[doc_id]
    return f"removed required document '{doc_id}' ({title})"


@op("set_field")
def set_field(case: Case, rng: random.Random, params: dict) -> str:
    path = params["path"]
    value = _resolve_value(case, params.get("value"))
    if not mutate_field(case, path, value):
        raise KeyError(f"set_field: cannot address {path!r}")
    return f"set {path} = {value!r}"


@op("scale_number")
def scale_number(case: Case, rng: random.Random, params: dict) -> str:
    factor = float(params.get("factor", 1.5))
    pattern = params.get("path") or params.get("paths") or "*"
    patterns = [pattern] if isinstance(pattern, str) else list(pattern)
    matched: list[str] = []
    for pat in patterns:
        matched.extend(resolve_glob(case, pat))
    matched = sorted(set(matched))
    if not matched:
        raise KeyError(f"scale_number: no fields match {patterns}")
    changed: list[str] = []
    for path in matched:
        v = read_field(case, path)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            new = v * factor
            mutate_field(case, path, int(round(new)) if isinstance(v, int) else new)
            changed.append(path)
    return f"scaled {changed} by {factor}"


@op("shift_date")
def shift_date(case: Case, rng: random.Random, params: dict) -> str:
    path = params["path"]
    days = int(params.get("days", 30))
    v = read_field(case, path)
    d = _dt.date.fromisoformat(str(v))
    new = (d + _dt.timedelta(days=days)).isoformat()
    mutate_field(case, path, new)
    return f"shifted {path}: {v} -> {new}"


@op("drop_signature")
def drop_signature(case: Case, rng: random.Random, params: dict) -> str:
    path = params.get("path", "application_form.signature_present")
    mutate_field(case, path, False)
    return f"signature dropped ({path}=false)"


def apply_plan(plan_path: Path, cases_dir: Path, out_dir: Path) -> list[Path]:
    """Execute an errorgen plan: source packet + named corruption ops -> cases."""
    with open(plan_path, encoding="utf-8") as f:
        plan = yaml.safe_load(f)
    src = cases_dir / plan["source"]
    with open(src, encoding="utf-8") as f:
        base = Case.model_validate(yaml.safe_load(f))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for step in plan.get("ops", []):
        rng = random.Random(step.get("seed", hash(step["id"]) & 0xFFFF))
        case = copy.deepcopy(base)
        fn = OPS.get(step["op"])
        if fn is None:
            raise KeyError(f"unknown errorgen op {step['op']!r} (known: {sorted(OPS)})")
        desc = fn(case, rng, step.get("params", {}))
        case.id = f"{base.id}__{step['id']}"
        case.generated_by = [f"{step['op']}: {desc}"]
        case.notes = step.get("note")
        dest = out_dir / f"{case.id}.yaml"
        dest.write_text(yaml.safe_dump(case.model_dump(exclude_none=True),
                                       allow_unicode=True, sort_keys=False), encoding="utf-8")
        written.append(dest)
    return written
