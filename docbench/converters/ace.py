"""Converter: Fujitsu ACE compliance scenarios -> docbench conformance cases.

ACE gives scenario + governing clauses + scenario-level label
(Compliant / Non-Compliant / Not-Applicable). YAGNI cut for the S2 bridge:
binary slice only (Not-Applicable dropped — needs a third disposition),
disposition-scope gold (no per-rule gold exists in the source).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..config import REPO_ROOT
from ..schemas import Case, CaseDocument, Rule, Ruleset

LABEL_MAP = {"Compliant": "accept", "Non-Compliant": "needs_correction"}


def convert_ace(source: Path, n: int, cases_dir: Path, ruleset_dir: Path,
                balanced: bool = True) -> list[tuple[str, str]]:
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    if balanced:
        pos = [s for s in scenarios if s["gd_tr"] == "Compliant"]
        neg = [s for s in scenarios if s["gd_tr"] == "Non-Compliant"]
        picked: list[dict] = []
        while len(picked) < n and (pos or neg):
            for buf in (neg, pos):  # non-compliant first: defects are the point
                if buf and len(picked) < n:
                    picked.append(buf.pop(0))
    else:
        picked = [s for s in scenarios if s["gd_tr"] in LABEL_MAP][:n]

    cases_dir.mkdir(parents=True, exist_ok=True)
    ruleset_dir.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, str]] = []
    for i, s in enumerate(picked):
        label = LABEL_MAP[s["gd_tr"]]
        rs_id = f"ace-{i:04d}"
        case_id = f"ace_{i:04d}"
        rules = [Rule(id=cid, description=text, severity="major",
                      category="contract_clause")
                 for cid, text in sorted(s["clauses"].items())]
        ruleset = Ruleset(id=rs_id, version="ace1", institution="ACE (Fujitsu)", rules=rules)
        (ruleset_dir / f"{rs_id}.yaml").write_text(
            yaml.safe_dump(ruleset.model_dump(exclude_none=True),
                           allow_unicode=True, sort_keys=False), encoding="utf-8")
        clause_blob = "\n\n".join(f"[{cid}] {text}" for cid, text in sorted(s["clauses"].items()))
        doc = CaseDocument(kind="agreement", title=f"ACE scenario {i}",
                           text=f"AGREEMENT CLAUSES (governing rules):\n{clause_blob}\n\n"
                                f"SCENARIO UNDER REVIEW:\n{s['scenario_text']}")
        case = Case(id=case_id, benchmark="conformance", ruleset=rs_id,
                    documents={"agreement": doc},
                    expected_disposition=label, gold_scope="disposition",
                    notes=f"ACE source label: {s['gd_tr']}")
        (cases_dir / f"{case_id}.yaml").write_text(
            yaml.safe_dump(case.model_dump(exclude_none=True),
                           allow_unicode=True, sort_keys=False), encoding="utf-8")
        written.append((case_id, label))
    return written
