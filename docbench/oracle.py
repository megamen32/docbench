"""Deterministic oracle: flatten a packet into facts and evaluate rules exactly.

The oracle is the canonical ground-truth generator. errorgen only mutates
packets; gold findings and disposition are always recomputed here, so the
benchmark can never drift from its own rules.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from .schemas import Case, Condition, Disposition, Finding, Rule, Ruleset

MISSING = object()


def flatten_case(case: Case) -> dict[str, Any]:
    """Flat dotted fact space for a packet: <doc>.<field>, table totals/rows,
    presence flags, and the whole doc count."""
    flat: dict[str, Any] = {}
    for doc_id, doc in case.documents.items():
        flat[f"documents.{doc_id}.present"] = True
        for k, v in doc.fields.items():
            flat[f"{doc_id}.{k}"] = v
        if doc.table is not None:
            for tk, tv in doc.table.totals.items():
                flat[f"{doc_id}.totals.{tk}"] = tv
            for row in doc.table.rows:
                # addressable as <doc>.row.<key-column-value>.<column>
                if "category" in row:
                    for col, val in row.items():
                        if col != "category":
                            flat[f"{doc_id}.row.{row['category']}.{col}"] = val
    return flat


def _coerce_pair(a: Any, b: Any) -> tuple[Any, Any] | None:
    """Best common type for comparison: bool stays bool, numbers go float,
    ISO dates (YYYY-MM-DD) stay strings and compare lexically, else strings."""
    if isinstance(a, bool) or isinstance(b, bool):
        return (a, b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return (float(a), float(b))
    if isinstance(a, str) and isinstance(b, str):
        for s in (a, b):
            try:
                _dt.date.fromisoformat(s)
            except ValueError:
                return (a, b)
        return (a, b)
    if isinstance(a, str) != isinstance(b, str):
        try:
            return (float(a), float(b))
        except (TypeError, ValueError):
            return None
    return (a, b)


def _values_equal(a: Any, b: Any) -> bool:
    pair = _coerce_pair(a, b)
    if pair is None:
        return False
    return pair[0] == pair[1]


def _get(flat: dict[str, Any], path: str) -> Any:
    if path in flat:
        return flat[path]
    # one-level nested fallback: a.b.c -> walk dicts
    cur: Any = flat
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


def evaluate_condition(cond: Condition, flat: dict[str, Any]) -> tuple[bool, Any, Any]:
    """Returns (passed, expected, observed). observed is MISSING-aware."""
    op = cond.op
    if op == "consistent":
        paths = cond.fields or []
        vals = [_get(flat, p) for p in paths]
        present = [v for v in vals if v is not MISSING]
        expected = "all equal"
        if len(present) < 2:
            return False, expected, "not enough values"
        ok = all(_values_equal(present[0], v) for v in present[1:])
        return ok, expected, present

    val = _get(flat, cond.field or "")
    target = cond.value

    if op in ("exists", "not_exists"):
        exists = val is not MISSING and val is not None and val != ""
        return (exists if op == "exists" else not exists), target, _obs(val)

    if op in ("in", "not_in"):
        if val is MISSING:
            return False, target, "missing"
        hit = any(_values_equal(val, t) for t in (target or []))
        return (hit if op == "in" else not hit), target, _obs(val)

    if val is MISSING:
        return False, target, "missing"
    pair = _coerce_pair(val, target)
    if pair is None:
        return False, target, _obs(val)
    a, b = pair
    if op == "eq":
        return a == b, target, _obs(val)
    if op == "ne":
        return a != b, target, _obs(val)
    try:
        if op in ("lt", "before"):
            return a < b, target, _obs(val)
        if op in ("le",):
            return a <= b, target, _obs(val)
        if op in ("gt", "after"):
            return a > b, target, _obs(val)
        if op in ("ge",):
            return a >= b, target, _obs(val)
    except TypeError:
        return False, target, _obs(val)
    raise ValueError(f"unsupported op {op}")


def _obs(v: Any) -> Any:
    return "missing" if v is MISSING else v


def _evidence_for(rule: Rule, cond: Condition, flat: dict[str, Any]) -> dict[str, str]:
    """Locate the document the condition's field points at."""
    if cond.op == "consistent" and cond.fields:
        base = cond.fields[0].split(".")[0]
    else:
        base = (cond.field or "").split(".")[0]
    locator = cond.fields[0] if cond.op == "consistent" and cond.fields else cond.field
    return {"document": base if base else None, "locator": locator, "quote": None}


def oracle_findings(case: Case, ruleset: Ruleset) -> list[Finding]:
    flat = flatten_case(case)
    out: list[Finding] = []
    for rule in ruleset.rules:
        if rule.condition is None:
            out.append(Finding(rule_id=rule.id, status="not_applicable",
                               expected=rule.description, observed="rule has no machine condition"))
            continue
        passed, expected, observed = evaluate_condition(rule.condition, flat)
        out.append(Finding(
            rule_id=rule.id,
            status="ok" if passed else "violation",
            expected=expected,
            observed=observed,
            evidence=None if passed else _evidence_for(rule, rule.condition, flat),
        ))
    return out


def disposition_for(findings: list[Finding], rules: list[Rule]) -> Disposition:
    sev = {r.id: r.severity for r in rules}
    if any(f.status == "violation" and sev.get(f.rule_id) == "critical" for f in findings):
        return "reject"
    if any(f.status == "violation" for f in findings):
        return "needs_correction"
    return "accept"


def gold_for(case: Case, ruleset: Ruleset) -> tuple[list[Finding], Disposition]:
    """Manual gold wins when declared; otherwise the oracle recomputes it."""
    if case.expected_findings:
        disp = case.expected_disposition or disposition_for(case.expected_findings, ruleset.rules)
        return case.expected_findings, disp
    findings = oracle_findings(case, ruleset)
    return findings, disposition_for(findings, ruleset.rules)
