from docbench.errorgen import mutate_field
from docbench.oracle import disposition_for, flatten_case, oracle_findings


def _viol(findings):
    return sorted(f.rule_id for f in findings if f.status == "violation")


def test_flatten_valid_packet(valid_case):
    flat = flatten_case(valid_case)
    assert flat["application_form.months_registered"] == 26
    assert flat["budget.totals.total"] == 84200
    assert flat["budget.row.equipment.share_pct"] == 29.9
    assert flat["documents.registration_cert.present"] is True
    assert flat["finance_statement.period"] == "FY2025"


def test_valid_packet_all_ok(valid_case, ruleset):
    findings = oracle_findings(valid_case, ruleset)
    assert _viol(findings) == []
    assert disposition_for(findings, ruleset.rules) == "accept"


def test_missing_budget_cascades(valid_case, ruleset):
    case = valid_case.model_copy(deep=True)
    del case.documents["budget"]
    assert _viol(oracle_findings(case, ruleset)) == ["R002", "R003", "R005", "R010"]
    assert disposition_for(oracle_findings(case, ruleset), ruleset.rules) == "reject"


def test_over_budget(valid_case, ruleset):
    case = valid_case.model_copy(deep=True)
    mutate_field(case, "budget.totals.total", 134720)
    assert _viol(oracle_findings(case, ruleset)) == ["R002", "R010"]
    assert disposition_for(oracle_findings(case, ruleset), ruleset.rules) == "needs_correction"


def test_minor_only_is_needs_correction(valid_case, ruleset):
    case = valid_case.model_copy(deep=True)
    mutate_field(case, "finance_statement.period", "FY2024")
    assert _viol(oracle_findings(case, ruleset)) == ["R011"]
    assert disposition_for(oracle_findings(case, ruleset), ruleset.rules) == "needs_correction"


def test_date_comparison_lexical_iso(valid_case, ruleset):
    case = valid_case.model_copy(deep=True)
    mutate_field(case, "application_form.submission_date", "2026-10-27")
    assert _viol(oracle_findings(case, ruleset)) == ["R008"]
