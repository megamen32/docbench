"""Strict scoring: the metrics that translate directly into headcount/economics."""
from __future__ import annotations

from typing import Any, Optional

from .schemas import Disposition, Finding, Prediction, Rule, Severity


def _viol(findings: list[Finding]) -> dict[str, Finding]:
    return {f.rule_id: f for f in findings if f.status == "violation"}


def findings_prf(gold: list[Finding], pred: list[Finding]) -> dict[str, float]:
    g, p = _viol(gold), _viol(pred)
    tp = len(set(g) & set(p))
    precision = tp / len(p) if p else (1.0 if not g else 0.0)
    recall = tp / len(g) if g else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp,
            "gold_violations": len(g), "pred_violations": len(p)}


def grounded_prf(gold: list[Finding], pred: list[Finding]) -> dict[str, float]:
    """A true positive counts as grounded only if the predicted evidence points
    at the same document as the gold evidence (when gold declares one)."""
    g, p = _viol(gold), _viol(pred)
    grounded = 0
    for rid in set(g) & set(p):
        ge, pe = g[rid].evidence, p[rid].evidence
        if pe is None or not (pe.document or pe.locator or pe.quote):
            continue
        if ge is None or ge.document is None or pe.document == ge.document:
            grounded += 1
    denom_g = len(g)
    denom_p = len(p)
    return {
        "grounded_tp": grounded,
        "grounding_precision": grounded / denom_p if denom_p else 1.0,
        "grounding_recall": grounded / denom_g if denom_g else 1.0,
    }


def critical_recall(gold: list[Finding], pred: list[Finding], sev: dict[str, Severity]) -> float:
    crit = [rid for rid in _viol(gold) if sev.get(rid) == "critical"]
    if not crit:
        return 1.0
    hit = sum(1 for rid in crit if rid in _viol(pred))
    return hit / len(crit)


def case_exact_pass(pred: Prediction, gold: list[Finding], gold_disp: Disposition) -> bool:
    if pred.parse_error or pred.disposition != gold_disp:
        return False
    g = {(f.rule_id, f.status) for f in gold}
    p = {(f.rule_id, f.status) for f in pred.findings}
    return g == p


def false_accept(pred: Prediction, gold_disp: Disposition) -> bool:
    """A defective packet (gold != accept) accepted automatically."""
    return gold_disp != "accept" and pred.disposition == "accept"


def false_reject(pred: Prediction, gold_disp: Disposition) -> bool:
    """A correct packet (gold == accept) not accepted."""
    return gold_disp == "accept" and pred.disposition != "accept"


_MISSING = object()


def extraction_prf(gold_fields: dict[str, Any], pred_fields: dict[str, Any]) -> dict[str, float]:
    """Value F1 over the union of keys: exact match with type coercion,
    null-vs-missing distinction preserved, invented keys penalized."""
    keys = set(gold_fields) | set(pred_fields)
    if not keys:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0}
    tp = 0
    for k in keys:
        g = gold_fields.get(k, _MISSING)
        p = pred_fields.get(k, _MISSING)
        if g is _MISSING or p is _MISSING:
            continue
        if _eq(g, p):
            tp += 1
    precision = tp / len(pred_fields) if pred_fields else 0.0
    recall = tp / len(gold_fields) if gold_fields else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp,
            "gold_fields": len(gold_fields), "pred_fields": len(pred_fields)}


def _eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    if isinstance(a, str) and isinstance(b, str):
        return a.strip() == b.strip()
    if a is None or b is None:
        return a is b
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def rules_prf(gold: list[Rule], pred: list[Rule]) -> dict[str, Any]:
    """Rule extraction score: match rules by normalized machine triple
    (field, op, value); severity accuracy measured on matched pairs."""
    def triple(r: Rule) -> Optional[tuple]:
        if r.condition is None:
            return None
        c = r.condition
        v = c.value
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return (c.field, c.op, tuple(v) if isinstance(v, list) else v)

    def triples(rs: list[Rule]) -> list[tuple]:
        return [t for t in (triple(r) for r in rs) if t is not None]

    g_by_t: dict[tuple, Rule] = {}
    for r in gold:
        t = triple(r)
        if t is not None:
            g_by_t.setdefault(t, r)
    p_by_t: dict[tuple, Rule] = {}
    for r in pred:
        t = triple(r)
        if t is not None:
            p_by_t.setdefault(t, r)

    matched = set(g_by_t) & set(p_by_t)
    tp = len(matched)
    precision = tp / len(p_by_t) if p_by_t else (1.0 if not g_by_t else 0.0)
    recall = tp / len(g_by_t) if g_by_t else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    sev_ok = sum(1 for t in matched if g_by_t[t].severity == p_by_t[t].severity)
    return {
        "precision": precision, "recall": recall, "f1": f1, "tp": tp,
        "gold_rules": len(g_by_t), "pred_rules": len(p_by_t),
        "severity_accuracy": sev_ok / tp if tp else 0.0,
        "unmatched_gold": sorted(str(t) for t in set(g_by_t) - matched),
        "unmatched_pred": sorted(str(t) for t in set(p_by_t) - matched),
    }
