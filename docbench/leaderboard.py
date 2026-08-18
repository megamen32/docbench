"""Static, local, auditable leaderboard for saved DocBench runs."""
from __future__ import annotations

import html
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


STANDARD_SUITES = {
    "cases/seed-grant": ("Grant conformance", 10),
    "cases/seed-policy": ("Policy rule extraction", 12),
    "cases/ace-test": ("ACE conformance", 30),
}
STANDARD_CASE_COUNT = sum(expected for _, expected in STANDARD_SUITES.values())


def _relative_cases_path(value: str) -> str:
    value = value.replace("\\", "/")
    for suffix in STANDARD_SUITES:
        if value.endswith(suffix):
            return suffix
    return value


def _read_runs(runs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("**/results.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not isinstance(data.get("summary"), dict):
            continue
        data["_path"] = path
        data["_cases_key"] = _relative_cases_path(str(data.get("cases_path", "")))
        rows.append(data)
    return rows


def _newest_per_model_suite(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    newest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("model", "")), str(row["_cases_key"]))
        current = newest.get(key)
        if current is None or str(row.get("ts", "")) >= str(current.get("ts", "")):
            newest[key] = row
    return list(newest.values())


def _href(from_path: Path, target: Path) -> str:
    return Path(os.path.relpath(target, from_path.parent)).as_posix()


def _run_card(row: dict[str, Any], card_path: Path, leaderboard_path: Path) -> None:
    result_path = Path(row["_path"])
    transcript = result_path.with_name("transcript.json")
    report = result_path.with_name("report.md")
    summary = row["summary"]
    meta = {
        key: row.get(key)
        for key in ("ts", "model", "model_alias", "provider", "provider_label", "benchmark",
                    "cases_path", "effort", "request_extra", "served_models", "reasoning",
                    "reasoning_note", "price_source")
    }
    metrics = {
        key: summary.get(key)
        for key in ("n_cases", "n_scored", "n_errors", "case_pass_rate", "finding_precision",
                    "finding_recall", "finding_f1", "extraction_f1", "grounding_recall",
                    "latency_p50_s", "wall_time_s", "total_cost_rub", "cost_per_case_rub",
                    "tokens")
    }
    transcript_link = (
        f'<a href="{html.escape(_href(card_path, transcript))}">transcript.json</a>'
        if transcript.is_file() else
        '<span class="missing">legacy run: transcript was not retained</span>'
    )
    card_path.write_text(f"""<!doctype html>
<meta charset="utf-8"><title>DocBench run</title>
<style>body{{font:15px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}}pre{{white-space:pre-wrap;background:#f6f8fa;padding:1rem}}a{{color:#0969da}}.missing{{color:#a40e26}}</style>
<p><a href="{html.escape(_href(card_path, leaderboard_path))}">← leaderboard</a></p>
<h1>{html.escape(str(row.get('model', 'unknown')))}</h1>
<p>Artifacts: {transcript_link} · <a href="{html.escape(_href(card_path, result_path))}">results.json</a> · <a href="{html.escape(_href(card_path, report))}">report.md</a></p>
<h2>Run metadata</h2><pre>{html.escape(json.dumps(meta, ensure_ascii=False, indent=2))}</pre>
<h2>Scores</h2><pre>{html.escape(json.dumps(metrics, ensure_ascii=False, indent=2))}</pre>
""", encoding="utf-8")


def _score(value: Any) -> str:
    return "—" if value is None else f"{float(value):.4f}"


def _rub(value: Any) -> str:
    return "—" if value is None else f"{float(value):.2f} ₽"


def _count(value: Any) -> str:
    return "—" if value is None else f"{int(value):,}"


def _seconds(value: Any) -> str:
    return "—" if value is None else f"{float(value):.1f} s"


def _tokens(row: dict[str, Any], key: str) -> Any:
    tokens = row["summary"].get("tokens")
    return tokens.get(key) if isinstance(tokens, dict) else None


def _wall_time(row: dict[str, Any]) -> Any:
    return row["summary"].get("wall_time_s", row.get("wall_time_s"))


def _all_or_missing(values: list[Any]) -> Any:
    """Aggregate only complete measurements; partial totals would look authoritative."""
    return None if not values or any(value is None for value in values) else sum(values)


def _table(rows: list[dict[str, Any]], output: Path) -> str:
    parts = [
        "<table><thead><tr><th>Model</th><th>Cases</th><th>Pass rate</th><th>Errors</th><th>F1</th>"
        "<th>Cost, RUB</th><th>RUB / case</th><th>Input tokens</th><th>Output tokens</th>"
        "<th>Cache tokens</th><th>Reasoning tokens</th><th>API latency p50</th><th>Wall time</th>"
        "<th>Transcript</th></tr></thead><tbody>"
    ]
    for row in sorted(rows, key=lambda x: (x["summary"].get("case_pass_rate") or -1), reverse=True):
        result_path = Path(row["_path"])
        card = result_path.with_name("run.html")
        _run_card(row, card, output)
        transcript = result_path.with_name("transcript.json")
        summary = row["summary"]
        parts.append(
            "<tr class=clickable data-href=\"%s\"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(_href(output, card)), html.escape(str(row.get("model", ""))),
                summary.get("n_cases", "—"), _score(summary.get("case_pass_rate")),
                summary.get("n_errors", "—"),
                _score(summary.get("finding_f1") or summary.get("extraction_f1")),
                _rub(summary.get("total_cost_rub")), _rub(summary.get("cost_per_case_rub")),
                _count(_tokens(row, "input_tokens")), _count(_tokens(row, "output_tokens")),
                _count(_tokens(row, "cache_input_tokens")), _count(_tokens(row, "reasoning_tokens")),
                _seconds(summary.get("latency_p50_s")), _seconds(_wall_time(row)),
                "yes" if transcript.is_file() else "legacy / no",
            )
        )
    return "".join(parts) + "</tbody></table>"


def _overall_table(rows: list[dict[str, Any]]) -> str:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model[str(row.get("model", ""))].append(row)
    parts = [
        "<table><thead><tr><th>Model</th><th>Coverage</th><th>Weighted pass rate</th><th>Comparable</th>"
        "<th>Cost, RUB</th><th>RUB / case</th><th>Input tokens</th><th>Output tokens</th>"
        "<th>Cache tokens</th><th>Reasoning tokens</th><th>API latency p50</th><th>Wall time</th>"
        "</tr></thead><tbody>"
    ]
    aggregates = []
    for model, model_rows in by_model.items():
        covered = sum(int(r["summary"].get("n_cases") or 0) for r in model_rows)
        passed = sum((r["summary"].get("case_pass_rate") or 0) * (r["summary"].get("n_cases") or 0) for r in model_rows)
        complete = covered == 52 and {r["_cases_key"] for r in model_rows} == set(STANDARD_SUITES)
        total_cost = _all_or_missing([r["summary"].get("total_cost_rub") for r in model_rows])
        token_totals = {
            key: _all_or_missing([_tokens(r, key) for r in model_rows])
            for key in ("input_tokens", "output_tokens", "cache_input_tokens", "reasoning_tokens")
        }
        latency_values = [r["summary"].get("latency_p50_s") for r in model_rows]
        latency_p50 = (
            sorted(latency_values)[len(latency_values) // 2]
            if latency_values and all(value is not None for value in latency_values) else None
        )
        wall_time = _all_or_missing([_wall_time(r) for r in model_rows])
        aggregates.append((model, covered, passed / covered if covered else None, complete, total_cost,
                           token_totals, latency_p50, wall_time))
    for model, covered, rate, complete, total_cost, token_totals, latency_p50, wall_time in sorted(
        aggregates, key=lambda x: (x[3], x[2] or -1), reverse=True
    ):
        parts.append("<tr><td>%s</td><td>%s / %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            html.escape(model), covered, STANDARD_CASE_COUNT, _score(rate), "yes" if complete else "partial — do not rank",
            _rub(total_cost), _rub(total_cost / covered if total_cost is not None and covered else None),
            _count(token_totals["input_tokens"]), _count(token_totals["output_tokens"]),
            _count(token_totals["cache_input_tokens"]), _count(token_totals["reasoning_tokens"]),
            _seconds(latency_p50), _seconds(wall_time),
        ))
    return "".join(parts) + "</tbody></table>"


def write_leaderboard(runs_dir: Path, output: Path) -> dict[str, Any]:
    """Generate a local HTML index and one clickable card per saved run."""
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_runs(runs_dir)
    standard = _newest_per_model_suite([r for r in rows if r["_cases_key"] in STANDARD_SUITES])
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in standard:
        groups[row["_cases_key"]].append(row)
    sections = ["<h2>Overall standard suite</h2>", _overall_table(standard)]
    for key, (name, expected) in STANDARD_SUITES.items():
        sections.extend([f"<h2>{html.escape(name)} · {expected} cases</h2>", _table(groups[key], output)])
    output.write_text(f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>DocBench leaderboard</title>
<style>body{{font:15px system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem}}table{{border-collapse:collapse;width:100%;margin-bottom:2rem}}th,td{{border:1px solid #d0d7de;padding:.45rem;text-align:left}}th{{background:#f6f8fa}}tr.clickable{{cursor:pointer}}tr.clickable:hover{{background:#ddf4ff}}.note{{color:#57606a}}</style>
<h1>DocBench leaderboard</h1>
<p class="note">Generated {html.escape(datetime.now().isoformat(timespec='seconds'))}. Standard rank requires all {STANDARD_CASE_COUNT} cases. Click a row for its metadata, scores, and transcript. Legacy runs are visibly marked because they predate transcript retention.</p>
{''.join(sections)}
<script>document.querySelectorAll('tr[data-href]').forEach(r=>r.onclick=()=>location.href=r.dataset.href)</script>
</html>""", encoding="utf-8")
    return {"runs": len(rows), "out": str(output)}
