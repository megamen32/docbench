"""Core pydantic schemas shared by both benchmarks, the oracle, and errorgen."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["critical", "major", "minor"]
FindingStatus = Literal["violation", "ok", "not_applicable"]
Disposition = Literal["accept", "needs_correction", "reject"]

ConditionOp = Literal[
    "eq", "ne", "lt", "le", "gt", "ge",
    "in", "not_in", "exists", "not_exists",
    "before", "after", "consistent",
]


class Condition(BaseModel):
    """Machine-checkable predicate over the flat extracted-fact space.

    `field` is a dotted path into the flattened packet facts, e.g.
    ``application_form.months_registered`` or ``documents.budget.present``.
    ``consistent`` compares all paths in `fields` for equality instead.
    """

    field: Optional[str] = None
    op: ConditionOp
    value: Any = None
    fields: Optional[list[str]] = None  # only for op == "consistent"

    def describe(self) -> str:
        if self.op == "consistent":
            return f"all of {self.fields} are consistent (equal)"
        return f"{self.field or '<missing>'} {self.op} {jsonish(self.value)}"


class Rule(BaseModel):
    id: str
    description: str
    severity: Severity = "major"
    category: Optional[str] = None
    condition: Optional[Condition] = None


class Ruleset(BaseModel):
    id: str
    version: str = "1.0"
    institution: str = "Institution"
    rules: list[Rule]


class Evidence(BaseModel):
    document: Optional[str] = None
    locator: Optional[str] = None
    quote: Optional[str] = None


class Finding(BaseModel):
    rule_id: str
    status: FindingStatus
    expected: Any = None
    observed: Any = None
    evidence: Optional[Evidence] = None


class TableDoc(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    totals: dict[str, Any] = Field(default_factory=dict)


class CaseDocument(BaseModel):
    kind: str = "text"            # form | table | certificate | statement | text
    title: Optional[str] = None
    fields: dict[str, Any] = Field(default_factory=dict)
    table: Optional[TableDoc] = None
    text: Optional[str] = None    # free-form prose (policy, narrative)


class Case(BaseModel):
    id: str
    benchmark: Literal["conformance", "rule_extraction"] = "conformance"
    ruleset: Optional[str] = None            # ruleset id for conformance
    policy_document: Optional[str] = None    # inline text for rule_extraction
    canonical_fields: Optional[list[str]] = None  # rule_extraction field registry
    documents: dict[str, CaseDocument] = Field(default_factory=dict)
    expected_findings: list[Finding] = Field(default_factory=list)  # manual gold; else oracle
    expected_disposition: Optional[Disposition] = None
    expected_rules: Optional[list[Rule]] = None   # rule_extraction gold
    generated_by: Optional[list[str]] = None      # errorgen operator names
    notes: Optional[str] = None


class Prediction(BaseModel):
    case_id: str
    ok: bool = False
    parse_error: Optional[str] = None
    extracted: dict[str, Any] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    disposition: Optional[str] = None
    rules: list[Rule] = Field(default_factory=list)  # rule_extraction output
    raw: Optional[str] = None
    usage: dict[str, Any] = Field(default_factory=dict)
    cost_usd: Optional[float] = None
    cost_is_estimate: bool = False
    latency_s: Optional[float] = None
    cache_hit: bool = False


def jsonish(v: Any) -> str:
    import json
    return json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
