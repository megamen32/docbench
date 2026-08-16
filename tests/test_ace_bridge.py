"""S2 bridge: ACE scenarios -> disposition-scope conformance cases."""
import json
from pathlib import Path

import pytest

from docbench.benchmarks.base import load_case, load_ruleset
from docbench.converters.ace import convert_ace
from docbench.oracle import gold_for

REPO = Path(__file__).resolve().parent.parent
ACE_TEST = REPO / "external/Fujitsu-Assessing-Compliance-in-Enterprise-Dataset/test.json"
pytestmark = pytest.mark.skipif(not ACE_TEST.is_file(), reason="ACE clone not present")


def test_convert_and_gold(tmp_path):
    written = convert_ace(ACE_TEST, n=4, cases_dir=tmp_path / "cases",
                          ruleset_dir=tmp_path / "rulesets")
    assert len(written) == 4
    labels = {c: d for c, d in written}
    assert set(labels.values()) <= {"accept", "needs_correction"}
    assert "needs_correction" in labels.values()  # balanced pick starts with defects
    for case_id, label in written:
        case = load_case(tmp_path / "cases" / f"{case_id}.yaml")
        ruleset = load_ruleset(tmp_path / "rulesets" / f"{case.ruleset}.yaml")
        assert case.gold_scope == "disposition"
        assert ruleset.rules, "clauses must become rules"
        findings, disp = gold_for(case, ruleset)
        assert findings == [] and disp == label


def test_disposition_scope_scoring_binary(tmp_path, ruleset):
    from docbench.benchmarks.conformance import ConformanceBenchmark
    import yaml as _yaml
    case = load_case(REPO / "cases/seed-grant/valid_full.yaml")
    case = case.model_copy(deep=True)
    case.gold_scope = "disposition"
    case.expected_disposition = "needs_correction"
    bench = ConformanceBenchmark(ruleset)
    gold = bench.gold_for(case)
    assert gold["scope"] == "disposition"
    # model says accept on a defective packet -> binary disagreement + FA
    scores = bench.score({"disposition": "accept", "findings": [], "extracted": {}},
                         gold, case)
    assert scores["ok"] is False and scores["false_accept"] is True
    # model says reject (still non-accept) -> binary agreement
    scores2 = bench.score({"disposition": "reject", "findings": [], "extracted": {}},
                          gold, case)
    assert scores2["ok"] is True and scores2["false_accept"] is False
