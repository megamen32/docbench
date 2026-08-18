"""Bench #3 — de-identified real-world IRI packet review.

The packet may be public after redaction, while the gold labels stay in a
caller-supplied file outside the repository.  Models never receive that file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..jsonutil import extract_json
from ..schemas import Case
from .base import Benchmark, render_docs


SYSTEM = """Ты независимый аудитор русскоязычной заявки на конкурс ИРИ.
Работай только с переданным обезличенным пакетом. Не используй интернет и не
выдумывай факты. Найди подтверждённые нарушения и несогласованности.

Верни только один валидный JSON-объект без Markdown, вступления или текста до и
после JSON:
{"findings":[{"field":"...","canonical":"...","requirement":"...","evidence":"...","fix":"..."}]}

Каждый finding — отдельное подтверждённое нарушение. `field` — точное поле ИРИ.
`canonical` должен начинаться ровно с «Необходимо доработать поле «<поле>».».
`requirement` — применимое требование, `evidence` — короткое доказательство с
файлом/страницей/полем, `fix` — минимальное исправление. Все значения — строки.
Если подтверждённых нарушений нет, верни {"findings":[]}. Не добавляй догадки,
таблицы, свободные рассуждения или сведения, которых нет в пакете."""

REQUIRED_KEYS = {"field", "canonical", "requirement", "evidence", "fix"}
CANONICAL_PREFIX = "Необходимо доработать поле «"


class IriReviewBenchmark(Benchmark):
    name = "iri_review"

    def __init__(self, gold_path: Path | None = None):
        if gold_path is None:
            raise ValueError("iri_review requires a private gold file; pass --gold")
        raw_bytes = gold_path.read_bytes()
        if raw_bytes.startswith(b"\x00GITCRYPT\x00"):
            raise RuntimeError("IRI gold is git-crypt locked; unlock the checkout first")
        raw = yaml.safe_load(raw_bytes.decode("utf-8"))
        self.gold_by_case = self._load_gold(raw)

    @staticmethod
    def _load_gold(raw: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(raw, dict):
            raise ValueError("IRI gold must be a YAML object")
        if isinstance(raw.get("cases"), dict):
            cases = raw["cases"]
        elif raw.get("case_id"):
            cases = {str(raw["case_id"]): raw}
        else:
            raise ValueError("IRI gold must contain case_id or cases")
        out: dict[str, dict[str, Any]] = {}
        for case_id, value in cases.items():
            if not isinstance(value, dict) or not isinstance(value.get("findings"), list):
                raise ValueError(f"IRI gold case {case_id!r} must contain findings list")
            out[str(case_id)] = value
        return out

    def gold_for(self, case: Case) -> dict[str, Any]:
        if case.id not in self.gold_by_case:
            raise KeyError(f"IRI gold has no case {case.id!r}")
        data = self.gold_by_case[case.id]
        return {
            "findings": data["findings"],
            "disposition": data.get("disposition", "needs_correction"),
        }

    def messages(self, case: Case, gold: Any) -> list[dict[str, str]]:
        user = (
            "ОБЕЗЛИЧЕННЫЙ ПАКЕТ ЗАЯВКИ:\n"
            + render_docs(case)
            + "\n\nПроверь пакет и верни JSON-объект строго по схеме."
        )
        return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]

    def parse(self, text: str, case: Case) -> tuple[Any, str | None]:
        obj = extract_json(text)
        if not isinstance(obj, dict) or not isinstance(obj.get("findings"), list):
            return None, "reply must contain a JSON findings list"
        findings: list[dict[str, str]] = []
        bad = 0
        for raw in obj["findings"]:
            if not isinstance(raw, dict) or set(raw) != REQUIRED_KEYS:
                bad += 1
                continue
            if any(not isinstance(raw[key], str) or not raw[key].strip() for key in REQUIRED_KEYS):
                bad += 1
                continue
            if not raw["canonical"].startswith(CANONICAL_PREFIX):
                bad += 1
                continue
            findings.append({key: raw[key].strip() for key in REQUIRED_KEYS})
        err = f"{bad} malformed findings dropped" if bad else None
        return {"findings": findings, "disposition": "needs_correction" if findings else "accept"}, err

    @staticmethod
    def _haystack(pred: dict[str, str]) -> str:
        return " ".join(pred.values()).casefold()

    @staticmethod
    def _matches(gold_finding: dict[str, Any], pred: dict[str, str]) -> bool:
        haystack = IriReviewBenchmark._haystack(pred)
        groups = gold_finding.get("match_groups") or []
        if not groups:
            field = str(gold_finding.get("field", "")).casefold()
            return bool(field and field in haystack)
        return all(
            any(str(term).casefold() in haystack for term in group)
            for group in groups
            if isinstance(group, list) and group
        )

    def score(self, pred: Any, gold: Any, case: Case) -> dict[str, Any]:
        predictions = pred["findings"]
        gold_findings = gold["findings"]
        matched_ids: list[str] = []
        used_predictions: set[int] = set()
        for index, expected in enumerate(gold_findings):
            match = next(
                (i for i, candidate in enumerate(predictions)
                 if i not in used_predictions and self._matches(expected, candidate)),
                None,
            )
            if match is not None:
                used_predictions.add(match)
                matched_ids.append(str(expected.get("id", f"IRI-{index + 1:03d}")))
        points = len(matched_ids)
        maximum = len(gold_findings)
        precision = points / len(predictions) if predictions else (1.0 if not maximum else 0.0)
        recall = points / maximum if maximum else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        missing = [str(f.get("id", f"IRI-{i + 1:03d}")) for i, f in enumerate(gold_findings)
                   if str(f.get("id", f"IRI-{i + 1:03d}")) not in matched_ids]
        return {
            "ok": points == maximum,
            "finding_precision": round(precision, 4),
            "finding_recall": round(recall, 4),
            "finding_f1": round(f1, 4),
            "critical_recall": None,
            "grounding_precision": None,
            "grounding_recall": None,
            "extraction_f1": None,
            "false_accept": maximum > 0 and not predictions,
            "false_reject": maximum == 0 and bool(predictions),
            "pred_disposition": pred["disposition"],
            "gold_disposition": gold["disposition"],
            "gold_points": points,
            "gold_max": maximum,
            "matched_gold_ids": matched_ids,
            "missing_gold_ids": missing,
            "false_positive_findings": max(0, len(predictions) - points),
        }
