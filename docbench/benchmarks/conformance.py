"""Bench #1 — conformance: packet + canonical ruleset -> findings/evidence/disposition."""
from __future__ import annotations

from typing import Any

import yaml

from .. import metrics as M
from ..oracle import flatten_case, gold_for
from ..schemas import Case, Evidence, Finding, Ruleset
from .base import Benchmark, render_docs

SYSTEM = """You are a formal verification officer. You verify application packets \
against a canonical, versioned institutional ruleset. You behave like software: \
deterministic, grounded, no guessing.

Reply with ONE JSON object and nothing else, exactly this shape:
{
  "extracted": {"<canonical field>": <value or null>, ...},
  "findings": [
    {"rule_id": "<id>", "status": "violation|ok|not_applicable",
     "expected": <what the rule requires>, "observed": <what the packet shows>,
     "evidence": {"document": "<doc id>", "locator": "<field/sheet/section>", "quote": "<short verbatim quote>"}}
  ],
  "disposition": "accept|needs_correction|reject"
}

Hard requirements:
- Report EVERY rule of the ruleset exactly once, same rule_ids, in order.
- Fill every canonical field listed in the task; use null when the packet does not state it. Never invent values.
- "violation" REQUIRES non-null evidence (document id + locator or verbatim quote) that grounds it in the packet.
- "evidence" is one object; for cross-document rules use an ARRAY of objects, one per document involved.
- Use "not_applicable" only when the rule genuinely cannot apply; say why in "observed".
- disposition: "reject" if any critical violation, "needs_correction" if any non-critical violation, "accept" otherwise.
- Dates are ISO YYYY-MM-DD; money values are plain numbers without symbols or separators.
- Emit strictly valid JSON: no trailing commas, no comments, double quotes everywhere.
"""


class ConformanceBenchmark(Benchmark):
    name = "conformance"

    def __init__(self, ruleset: Ruleset):
        self.ruleset = ruleset
        self.canonical_fields = self._canonical_fields(ruleset)

    @staticmethod
    def _canonical_fields(ruleset: Ruleset) -> list[str]:
        fields: list[str] = []
        for r in ruleset.rules:
            c = r.condition
            if c is None:
                continue
            if c.op == "consistent":
                fields.extend(p for p in (c.fields or []) if p not in fields)
            elif c.field and c.field not in fields:
                fields.append(c.field)
        return fields

    def gold_for(self, case: Case) -> dict[str, Any]:
        findings, disp = gold_for(case, self.ruleset)
        flat = flatten_case(case)
        gold_fields = {k: flat.get(k) for k in self.canonical_fields}
        return {"findings": findings, "disposition": disp, "gold_fields": gold_fields,
                "severity": {r.id: r.severity for r in self.ruleset.rules}}

    def messages(self, case: Case, gold: Any) -> list[dict[str, str]]:
        rules_blob = yaml.safe_dump(
            [{"id": r.id, "severity": r.severity, "category": r.category,
              "description": r.description,
              "machine": r.condition.model_dump(exclude_none=True) if r.condition else None}
             for r in self.ruleset.rules],
            allow_unicode=True, sort_keys=False)
        user = (
            f"RULESET {self.ruleset.id} v{self.ruleset.version} ({self.ruleset.institution}):\n"
            f"{rules_blob}\n"
            f"CANONICAL FIELDS to extract (fill each, null if absent):\n"
            + "\n".join(f"- {f}" for f in self.canonical_fields)
            + "\n\nAPPLICATION PACKET:\n" + render_docs(case)
            + '\n\nVerify every rule. Reply with the JSON object only.'
        )
        return [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user}]

    def parse(self, text: str, case: Case) -> tuple[Any, str | None]:
        from ..jsonutil import extract_json
        obj = extract_json(text)
        if obj is None:
            return None, "no JSON object in reply"
        findings: list[Finding] = []
        bad = 0
        for raw in obj.get("findings", []) or []:
            try:
                raw = dict(raw)
                ev = raw.get("evidence")
                if isinstance(ev, list):
                    ev = ev[0] if ev else None
                if ev is not None:
                    raw["evidence"] = Evidence.model_validate(ev) if isinstance(ev, dict) else None
                findings.append(Finding.model_validate(raw))
            except Exception:
                bad += 1
        err = f"{bad} malformed findings dropped" if bad else None
        pred = {
            "extracted": {k: v for k, v in (obj.get("extracted") or {}).items()},
            "findings": findings,
            "disposition": obj.get("disposition"),
        }
        return pred, err

    def score(self, pred: Any, gold: Any, case: Case) -> dict[str, Any]:
        sev = gold["severity"]
        f = M.findings_prf(gold["findings"], pred["findings"])
        g = M.grounded_prf(gold["findings"], pred["findings"])
        e = M.extraction_prf(gold["gold_fields"], pred["extracted"])
        ok = (
            pred["disposition"] == gold["disposition"]
            and {(x.rule_id, x.status) for x in gold["findings"]}
            == {(x.rule_id, x.status) for x in pred["findings"]}
        )
        return {
            "ok": ok,
            "finding_precision": f["precision"], "finding_recall": f["recall"], "finding_f1": f["f1"],
            "critical_recall": M.critical_recall(gold["findings"], pred["findings"], sev),
            "grounding_precision": g["grounding_precision"], "grounding_recall": g["grounding_recall"],
            "extraction_f1": e["f1"],
            "false_accept": M.false_accept(_P(pred), gold["disposition"]),
            "false_reject": M.false_reject(_P(pred), gold["disposition"]),
            "pred_disposition": pred["disposition"], "gold_disposition": gold["disposition"],
        }


class _P:
    """Tiny adapter so false_accept/false_reject keep their Prediction-based API."""
    def __init__(self, pred: dict):
        self.disposition = pred.get("disposition")
