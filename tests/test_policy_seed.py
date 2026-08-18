from pathlib import Path

from docbench.benchmarks.base import load_cases


REPO = Path(__file__).resolve().parent.parent


def test_russian_policy_seed_v1_has_twelve_loadable_cases():
    cases = load_cases(REPO / "cases" / "seed-policy")
    assert len(cases) == 12
    for _, case in cases:
        assert case.benchmark == "rule_extraction"
        assert case.policy_document and any("а" <= ch.lower() <= "я" for ch in case.policy_document)
        assert case.expected_rules
