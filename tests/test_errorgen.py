from pathlib import Path

from docbench.errorgen import apply_plan
from docbench.oracle import oracle_findings

REPO = Path(__file__).resolve().parent.parent
EXPECTED_VIOLATIONS = {
    "corr_missing_budget": ["R002", "R003", "R005", "R010"],
    "corr_missing_registration": ["R006"],
    "corr_over_budget": ["R002", "R010"],
    "corr_equipment_heavy": ["R003"],
    "corr_late_submission": ["R008"],
    "corr_unsigned": ["R009"],
    "corr_unregistered": ["R001"],
    "corr_sum_mismatch": ["R010"],
    "corr_wrong_period": ["R011"],
}


def test_apply_plan_produces_expected_gold(tmp_path, valid_case, ruleset):
    written = apply_plan(REPO / "cases" / "seed-grant" / "errorgen.yaml",
                         REPO / "cases" / "seed-grant", tmp_path)
    assert len(written) == len(EXPECTED_VIOLATIONS)
    for path in written:
        case_id = path.stem.split("__")[-1]
        assert case_id in EXPECTED_VIOLATIONS, case_id
        from docbench.benchmarks.base import load_case
        case = load_case(path)
        assert case.generated_by, f"{case_id} must record its mutation"
        violations = sorted(f.rule_id for f in oracle_findings(case, ruleset)
                            if f.status == "violation")
        assert violations == EXPECTED_VIOLATIONS[case_id], (
            f"{case_id}: got {violations}, want {EXPECTED_VIOLATIONS[case_id]}")
