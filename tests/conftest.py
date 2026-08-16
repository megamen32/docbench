from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from docbench.benchmarks.base import load_case, load_ruleset  # noqa: E402


@pytest.fixture(scope="session")
def ruleset():
    return load_ruleset(REPO / "rulesets" / "seed-grant-2026.1.yaml")


@pytest.fixture(scope="session")
def valid_case():
    return load_case(REPO / "cases" / "seed-grant" / "valid_full.yaml")
