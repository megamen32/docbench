"""Bench #2 — rule extraction: policy document -> machine-readable ruleset."""
from __future__ import annotations

from typing import Any

from .. import metrics as M
from ..schemas import Case, Condition, Rule
from .base import Benchmark

SYSTEM = """You are a policy formalization engine. You convert institutional \
policy documents into a machine-checkable ruleset. You extract only what the \
document actually states; you never add rules from general knowledge.

Reply with ONE JSON object and nothing else, exactly this shape:
{
  "ruleset_id": "<slug>",
  "rules": [
    {"description": "<one-line restatement of the rule>",
     "severity": "critical|major|minor",
     "category": "<short tag>",
     "condition": {"field": "<canonical field path>", "op": "<operator>", "value": <value or null>}
  }
}

Allowed operators: eq, ne, lt, le, gt, ge, in, not_in, exists, not_exists, before, after, consistent.
- Use ONLY the canonical field registry given in the task for `field`.
- `value` is the bound from the policy (number, ISO date, string, or list for in/not_in).
- For "the same value must appear in N places" rules use op=consistent with "fields": [...].
- Severity: critical = automatic rejection / hard eligibility; major = must fix; minor = formal or cosmetic.
"""

SYSTEM_RU = """Вы — система формализации политик. Вы превращаете институциональные
документы политики в машиночитаемый набор правил. Извлекайте только то, что прямо
сказано в документе; не добавляйте правила из общих знаний.

Верните РОВНО один JSON-объект и ничего больше, строго следующего вида:
{
  "ruleset_id": "<slug>",
  "rules": [
    {"description": "<однострочное изложение правила>",
     "severity": "critical|major|minor",
     "category": "<короткая метка>",
     "condition": {"field": "<канонический путь поля>", "op": "<оператор>", "value": <значение или null>}
  ]
}

Допустимые операторы: eq, ne, lt, le, gt, ge, in, not_in, exists, not_exists, before, after, consistent.
- Для field используйте ТОЛЬКО реестр канонических полей из задания.
- value — граница из политики: число, ISO-дата, строка или список для in/not_in.
- Для требования "одно и то же значение должно быть в N местах" используйте op=consistent и "fields": [...].
- Severity: critical = автоматический отказ / жёсткое требование допуска; major = нужно исправить; minor = формальное или косметическое требование.
"""


class RuleExtractionBenchmark(Benchmark):
    name = "rule_extraction"

    def __init__(self, locale: str = "en"):
        if locale not in {"en", "ru"}:
            raise ValueError(f"unsupported prompt locale {locale!r}")
        self.locale = locale

    def gold_for(self, case: Case) -> Any:
        return {"rules": case.expected_rules or []}

    def messages(self, case: Case, gold: Any) -> list[dict[str, str]]:
        registry = "\n".join(f"- {f}" for f in (case.canonical_fields or []))
        russian = self.locale == "ru"
        user = (
            ("РЕЕСТР КАНОНИЧЕСКИХ ПОЛЕЙ (используйте в condition только эти пути):\n"
             if russian else "CANONICAL FIELD REGISTRY (use only these paths in conditions):\n")
            + f"{registry}\n\n"
            + ("ДОКУМЕНТ ПОЛИТИКИ:\n" if russian else "POLICY DOCUMENT:\n")
            + f"{case.policy_document or '<empty>'}\n\n"
            + ("Извлеките полный набор правил. Ответьте только JSON-объектом."
               if russian else "Extract the complete ruleset. Reply with the JSON object only.")
        )
        return [{"role": "system", "content": SYSTEM_RU if russian else SYSTEM},
                {"role": "user", "content": user}]

    def parse(self, text: str, case: Case) -> tuple[Any, str | None]:
        from ..jsonutil import extract_json
        obj = extract_json(text)
        if obj is None:
            return None, "no JSON object in reply"
        rules: list[Rule] = []
        bad = 0
        for i, raw in enumerate(obj.get("rules", []) or []):
            try:
                raw = dict(raw)
                raw.setdefault("id", f"P{i + 1:03d}")
                cond = raw.get("condition")
                if isinstance(cond, dict):
                    raw["condition"] = Condition.model_validate(cond)
                rules.append(Rule.model_validate(raw))
            except Exception:
                bad += 1
        err = f"{bad} malformed rules dropped" if bad else None
        return {"rules": rules, "ruleset_id": obj.get("ruleset_id")}, err

    def score(self, pred: Any, gold: Any, case: Case) -> dict[str, Any]:
        s = M.rules_prf(gold["rules"], pred["rules"])
        s["ok"] = s["rule_exact_f1"] == 1.0
        s["pred_disposition"] = None
        s["gold_disposition"] = None
        s["false_accept"] = False
        s["false_reject"] = False
        s["finding_precision"] = s["precision"]
        s["finding_recall"] = s["recall"]
        s["finding_f1"] = s["f1"]
        s["critical_recall"] = None
        s["grounding_precision"] = None
        s["grounding_recall"] = None
        s["extraction_f1"] = None
        return s
