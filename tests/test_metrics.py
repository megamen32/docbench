from docbench import metrics as M
from docbench.schemas import Condition, Finding, Rule


def _f(rid, status="violation"):
    return Finding(rule_id=rid, status=status)


def test_findings_prf_perfect():
    gold = [_f("R1"), _f("R2")]
    pred = [_f("R1"), _f("R2")]
    m = M.findings_prf(gold, pred)
    assert (m["precision"], m["recall"], m["f1"]) == (1.0, 1.0, 1.0)


def test_findings_prf_miss_and_fp():
    gold = [_f("R1"), _f("R2")]
    pred = [_f("R1"), _f("R3")]  # one miss, one false alarm
    m = M.findings_prf(gold, pred)
    assert m["tp"] == 1
    assert abs(m["precision"] - 0.5) < 1e-9
    assert abs(m["recall"] - 0.5) < 1e-9


def test_critical_recall():
    gold = [_f("R1"), _f("R2"), _f("R3")]
    pred = [_f("R2")]
    sev = {"R1": "critical", "R2": "major", "R3": "critical"}
    assert M.critical_recall(gold, pred, sev) == 0.0
    pred2 = [_f("R1"), _f("R2")]
    assert M.critical_recall(gold, pred2, sev) == 0.5


class _P:
    def __init__(self, d):
        self.disposition = d


def test_false_accept_reject():
    assert M.false_accept(_P("accept"), "needs_correction") is True
    assert M.false_accept(_P("needs_correction"), "needs_correction") is False
    assert M.false_reject(_P("reject"), "accept") is True
    assert M.false_reject(_P("accept"), "accept") is False


def test_extraction_prf_null_vs_missing():
    gold = {"a": 1, "b": None}
    pred = {"a": 1.0, "b": None}
    m = M.extraction_prf(gold, pred)
    assert m["f1"] == 1.0  # numeric coercion, null matched
    pred2 = {"a": 1, "c": 9}  # b missing, c invented
    m2 = M.extraction_prf(gold, pred2)
    assert m2["tp"] == 1
    assert m2["precision"] < 1.0 and m2["recall"] < 1.0


def _rule(rid, field, op, value, sev="major"):
    return Rule(id=rid, description=rid, severity=sev,
                condition=Condition(field=field, op=op, value=value))


def test_rules_prf_exact_and_severity():
    gold = [_rule("G1", "f.age", "ge", 12, "critical"), _rule("G2", "f.total", "le", 100)]
    pred = [_rule("P1", "f.age", "ge", 12.0, "critical"), _rule("P2", "f.total", "le", 100)]
    m = M.rules_prf(gold, pred)
    assert m["f1"] == 1.0
    assert m["severity_accuracy"] == 1.0


def test_rules_prf_penalizes_invented():
    gold = [_rule("G1", "f.age", "ge", 12)]
    pred = [_rule("P1", "f.age", "ge", 12), _rule("P2", "f.made_up", "exists", None)]
    m = M.rules_prf(gold, pred)
    assert m["tp"] == 1
    assert m["precision"] < 1.0
    assert m["recall"] == 1.0


def test_rules_prf_handles_nested_json_value():
    gold = [_rule("G1", "f.age", "ge", 12)]
    pred = [_rule("P1", "f.age", "ge", {"unexpected": [1, 2]})]
    m = M.rules_prf(gold, pred)
    assert m["tp"] == 0
    assert m["precision"] == 0.0
