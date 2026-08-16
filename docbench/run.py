"""Run orchestration: cases -> model -> predictions -> strict metrics -> report."""
from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .benchmarks import BENCHMARKS
from .benchmarks.base import load_cases, ruleset_index
from .config import REPO_ROOT, resolve_model
from .models.openai_compat import OpenAICompatRunner
from .schemas import Prediction

VAR_DIR = REPO_ROOT / "var"
CACHE_DIR = VAR_DIR / "cache"
RUNS_DIR = VAR_DIR / "runs"


def _median(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 4) if xs else None


def run_benchmark(
    bench_key: str,
    model_key: str,
    cases_path: Path,
    *,
    ruleset_dir: Path | None = None,
    ruleset_id: str | None = None,
    limit: int | None = None,
    offline: bool = False,
    out_dir: Path | None = None,
    max_tokens: int = 8192,
    effort: str | None = None,
) -> dict[str, Any]:
    if bench_key not in BENCHMARKS:
        raise KeyError(f"unknown benchmark {bench_key!r}; known: {sorted(BENCHMARKS)}")
    spec = resolve_model(model_key, allow_missing_key=offline)
    extra_body = spec.effort_extra(effort)
    effort_label = effort or spec.effort_default or "provider-default"
    runner = OpenAICompatRunner(spec, cache_dir=CACHE_DIR, offline=offline)

    pairs = load_cases(Path(cases_path))
    if limit:
        pairs = pairs[:limit]

    per_case: list[dict[str, Any]] = []
    bench = None
    for path, case in pairs:
        if bench_key == "conformance":
            rid = ruleset_id or case.ruleset
            if not rid:
                raise ValueError(f"case {case.id}: no ruleset id")
            idx = ruleset_index(Path(ruleset_dir) if ruleset_dir else REPO_ROOT / "rulesets")
            if rid not in idx:
                raise KeyError(f"case {case.id}: ruleset {rid!r} not found in rulesets/")
            bench = BENCHMARKS[bench_key](idx[rid])
        else:
            bench = BENCHMARKS[bench_key]()
        gold = bench.gold_for(case)
        msgs = bench.messages(case, gold)
        t0 = time.monotonic()
        cost = 0.0
        cost_est = False
        comp = None
        payload, parse_err = None, None
        for attempt in range(2):
            try:
                comp = runner.complete(msgs, max_tokens=max_tokens, extra_body=extra_body)
            except Exception as e:  # network failure must not kill the run
                per_case.append({"case_id": case.id, "ok": False, "error": str(e)[:300],
                                 "cost_usd": None, "latency_s": None})
                comp = None
                break
            cost += comp.cost_usd or 0.0
            cost_est = cost_est or comp.cost_is_estimate
            payload, parse_err = bench.parse(comp.text, case)
            if payload is not None:
                break
            if attempt == 0:
                # reasoning models sometimes close <think> and stop: nudge once
                msgs = msgs + [{"role": "user",
                                "content": "Your previous reply contained no JSON. "
                                           "Output ONLY the JSON object now, starting with '{' "
                                           "with no preamble and no reasoning."}]
        if comp is None:
            continue
        wall = round(time.monotonic() - t0, 3)
        if payload is None:
            scores = {"ok": False, "parse_error": parse_err}
            pred_dump: dict[str, Any] = {"raw_head": (comp.text or "")[:400]}
        else:
            scores = bench.score(payload, gold, case)
            if parse_err:
                scores["parse_warning"] = parse_err
            pred_dump = _payload_dump(payload)
        row = {
            "case_id": case.id,
            "source": str(path),
            "generated_by": case.generated_by,
            **scores,
            "cost_usd": round(cost, 6) if cost else None,
            "cost_is_estimate": cost_est,
            "latency_s": comp.latency_s or wall,
            "cache_hit": comp.cache_hit,
            "usage": {**comp.usage, "served_model": comp.model},
        }
        per_case.append(row)

    summary = _aggregate(per_case)
    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "benchmark": bench_key,
        "model": spec.key,
        "model_alias": spec.alias,
        "provider": spec.provider,
        "provider_label": spec.provider_label,
        "effort": effort_label,
        "request_extra": extra_body,
        "quantization": spec.quantization,
        "quantization_note": ("providers do not expose served quantization via API; "
                              "pin provider+model+date and see served_models"),
        "served_models": sorted({c.get("usage", {}).get("served_model") for c in per_case
                                 if c.get("usage", {}).get("served_model")}),
        "price_source": spec.price_source,
        "cases_path": str(cases_path),
        "n_cases": len(per_case),
        "summary": summary,
        "cases": per_case,
    }
    out = out_dir or (RUNS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{bench_key}-{spec.key}")
    out.mkdir(parents=True, exist_ok=True)
    result["out_dir"] = str(out)
    (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render_markdown_report([result]), encoding="utf-8")
    return result


def _aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cases)
    errors = [c for c in cases if c.get("error") or c.get("parse_error")]
    scored = [c for c in cases if "finding_precision" in c]

    def mean(k: str) -> float | None:
        vals = [c[k] for c in scored if c.get(k) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    costs = [c["cost_usd"] for c in cases if c.get("cost_usd") is not None]
    lats = [c["latency_s"] for c in cases if c.get("latency_s") is not None]
    return {
        "n_cases": n,
        "n_scored": len(scored),
        "n_errors": len(errors),
        "case_pass_rate": round(sum(1 for c in cases if c.get("ok")) / n, 4) if n else None,
        "finding_precision": mean("finding_precision"),
        "finding_recall": mean("finding_recall"),
        "finding_f1": mean("finding_f1"),
        "critical_recall": mean("critical_recall"),
        "grounding_precision": mean("grounding_precision"),
        "grounding_recall": mean("grounding_recall"),
        "extraction_f1": mean("extraction_f1"),
        "false_accept_rate": round(sum(1 for c in scored if c.get("false_accept")) / len(scored), 4) if scored else None,
        "false_reject_rate": round(sum(1 for c in scored if c.get("false_reject")) / len(scored), 4) if scored else None,
        "cost_per_case_usd": round(sum(costs) / len(costs), 6) if costs else None,
        "cost_is_estimate": any(c.get("cost_is_estimate") for c in cases),
        "latency_p50_s": _median(lats),
        "total_cost_usd": round(sum(costs), 6) if costs else None,
    }


def _payload_dump(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    if "findings" in out:
        out["findings"] = [f.model_dump(exclude_none=True) if hasattr(f, "model_dump") else f
                           for f in out["findings"]]
    if "rules" in out:
        out["rules"] = [r.model_dump(exclude_none=True) if hasattr(r, "model_dump") else r
                        for r in out["rules"]]
    return out


def render_markdown_report(results: list[dict[str, Any]]) -> str:
    lines = ["# docbench report", ""]
    cols = ["model", "benchmark", "n_cases", "case_pass_rate", "finding_precision",
            "finding_recall", "critical_recall", "false_accept_rate", "false_reject_rate",
            "extraction_f1", "grounding_recall", "cost_per_case_usd", "latency_p50_s"]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for r in results:
        s = r.get("summary", {})
        row = []
        for c in cols:
            v = r.get(c, s.get(c))
            if isinstance(v, float):
                v = f"{v:.4f}" if v < 10 else f"{v:.1f}"
            row.append(str(v) if v is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    est = any(r.get("summary", {}).get("cost_is_estimate") for r in results)
    if est:
        lines.append("")
        lines.append("_Note: cost computed from catalog prices flagged as estimates; "
                     "override in docbench/models.yaml with invoiced prices._")
    lines.append("")
    for r in results:
        lines.append(f"## {r.get('model')} · {r.get('benchmark')} · {r.get('ts', '')}")
        lines.append("")
        for c in r.get("cases", []):
            flag = "✅" if c.get("ok") else "❌"
            gen = f" _({', '.join(c['generated_by'])})_" if c.get("generated_by") else ""
            lines.append(f"- {flag} `{c['case_id']}`{gen}"
                         f" — disp {c.get('pred_disposition')} vs {c.get('gold_disposition')}"
                         + (f", err: {c['error']}" if c.get("error") else "")
                         + (f", parse: {c['parse_error']}" if c.get("parse_error") else ""))
        lines.append("")
    return "\n".join(lines)
