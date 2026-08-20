"""Static, local, auditable leaderboard for saved DocBench runs."""
from __future__ import annotations

import html
import json
import os
import re
import shutil
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


def _inline_markdown(value: str) -> str:
    """Small, safe GFM subset for reports and model messages."""
    value = html.escape(value, quote=False)
    tick = chr(96)
    value = re.sub(tick + r"([^" + tick + r"\n]+)" + tick, r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda m: '<a href="%s" target="_blank" rel="noreferrer">%s</a>'
        % (html.escape(html.unescape(m.group(2)), quote=True), m.group(1)),
        value,
    )
    return value


def render_markdown(value: str) -> str:
    """Render a dependency-free, escaped Markdown view for the run card."""
    lines = (value or "").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    in_code = False
    code_lines: list[str] = []
    fence = chr(96) * 3

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append("<p>" + "<br>".join(_inline_markdown(line) for line in paragraph) + "</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            out.append(f"</{list_kind}>")
            list_kind = None

    i = 0
    while i < len(lines):
        line = lines[i]
        if in_code:
            if line.strip().startswith(fence):
                out.append('<pre class="md-code"><code>' + html.escape("\n".join(code_lines)) + "</code></pre>")
                in_code = False
                code_lines = []
            else:
                code_lines.append(line)
            i += 1
            continue
        if line.strip().startswith(fence):
            flush_paragraph(); close_list()
            in_code = True
            code_lines = []
            i += 1
            continue
        table_separator = r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$"
        if i + 1 < len(lines) and "|" in line and re.match(table_separator, lines[i + 1]):
            flush_paragraph(); close_list()
            def cells(raw: str) -> list[str]:
                return [part.strip() for part in raw.strip().strip("|").split("|")]
            headers = cells(line); i += 2
            body: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                body.append(cells(lines[i])); i += 1
            table = ["<table class=md-table><thead><tr>"]
            table.extend(f"<th>{_inline_markdown(cell)}</th>" for cell in headers)
            table.append("</tr></thead><tbody>")
            for row in body:
                table.append("<tr>" + "".join(f"<td>{_inline_markdown(cell)}</td>" for cell in row) + "</tr>")
            table.append("</tbody></table>")
            out.append("".join(table))
            continue
        heading = re.match(r"^\s*(#{1,4})\s+(.+?)\s*$", line)
        if heading:
            flush_paragraph(); close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline_markdown(heading.group(2))}</h{level}>")
            i += 1
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if bullet or ordered:
            flush_paragraph()
            wanted = "ol" if ordered else "ul"
            if list_kind != wanted:
                close_list(); list_kind = wanted; out.append(f"<{wanted}>")
            out.append(f"<li>{_inline_markdown((ordered or bullet).group(1))}</li>")
            i += 1
            continue
        if not line.strip():
            flush_paragraph(); close_list(); i += 1; continue
        close_list(); paragraph.append(line); i += 1
    if in_code:
        out.append('<pre class="md-code"><code>' + html.escape("\n".join(code_lines)) + "</code></pre>")
    flush_paragraph(); close_list()
    return "".join(out)


def _render_message(value: str) -> tuple[str, str]:
    """Return visible message HTML and collapsed thinking HTML."""
    def format_part(part: str) -> str:
        candidate = part.strip()
        if candidate and candidate[0] in "[{":
            try:
                parsed = json.loads(candidate)
            except (TypeError, json.JSONDecodeError):
                parsed = None
            if isinstance(parsed, (dict, list)):
                return '<pre class="md-code json-response"><code>' + html.escape(
                    json.dumps(parsed, ensure_ascii=False, indent=2)
                ) + "</code></pre>"
        return render_markdown(part)

    text = value or ""
    thinking: list[str] = []
    visible: list[str] = []
    pos = 0
    pattern = re.compile(r"<think>(.*?)(?:</think>|$)", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(text):
        visible.append(text[pos:match.start()])
        thinking.append(match.group(1).strip())
        pos = match.end()
        if not match.group(0).lower().endswith("</think>"):
            break
    visible.append(text[pos:])
    visible_html = format_part("\n\n".join(part for part in visible if part.strip()))
    thinking_html = "".join(
        '<details class="thinking"><summary>Thinking · скрыто по умолчанию</summary>'
        + format_part(part) + "</details>" for part in thinking if part
    )
    return visible_html, thinking_html


def _render_transcript_chat(transcript: dict[str, Any], result_cases: list[dict[str, Any]]) -> str:
    if not transcript or not transcript.get("cases"):
        return '<p class="muted">Транскрипт не сохранён или недоступен для этого запуска.</p>'
    result_by_id = {str(case.get("case_id")): case for case in result_cases}
    blocks: list[str] = []
    for case in transcript.get("cases", []):
        case_id = str(case.get("case_id", "unknown"))
        result = result_by_id.get(case_id, {})
        status = "OK" if result.get("ok") else ("ошибка" if result else "без оценки")
        attempts = case.get("attempts") or []
        inner = [f'<details class="transcript-case" open><summary><strong>{html.escape(case_id)}</strong><span class="chat-status">{html.escape(status)} · {len(attempts)} попыт.</span></summary>']
        for attempt in attempts:
            inner.append(f'<div class="attempt"><div class="attempt-label">Попытка {html.escape(str(attempt.get("attempt", "—")))}</div>')
            for message in attempt.get("messages") or []:
                role = str(message.get("role", "message"))
                content = str(message.get("content", ""))
                visible, thinking = _render_message(content)
                if role == "system":
                    inner.append('<details class="chat-message system"><summary>System prompt · скрыто по умолчанию</summary>' + visible + thinking + "</details>")
                else:
                    inner.append(f'<div class="chat-message {html.escape(role)}"><div class="chat-role">{html.escape(role)}</div>{visible}{thinking}</div>')
            response = attempt.get("response_text")
            if response is not None:
                visible, thinking = _render_message(str(response))
                inner.append('<div class="chat-message assistant"><div class="chat-role">assistant</div>' + (visible or '<p class="muted">Пустой финальный ответ</p>') + thinking + "</div>")
            usage = attempt.get("usage") or {}
            inner.append('<div class="attempt-meta">%s · %s токенов · %s</div>' % (
                html.escape(str(attempt.get("latency_s") or "—")),
                html.escape(str(usage.get("total_tokens") or "—")),
                "cache hit" if attempt.get("cache_hit") else "API"))
            inner.append("</div>")
        inner.append("</details>")
        blocks.append("".join(inner))
    return "<div class=transcript-chat>" + "".join(blocks) + "</div>"


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
    refusals = [str(case.get("case_id")) for case in row.get("cases", [])
                if case.get("response_kind") == "refusal"]
    response_contract = (
        "<p>Model refusal (instead of the required JSON): "
        + ", ".join(html.escape(case_id) for case_id in refusals) + "</p>"
        if refusals else ""
    )
    transcript_link = (
        f'<a class=button href="{html.escape(_href(card_path, transcript))}">transcript.json ↗</a>'
        if transcript.is_file() else
        '<span class="missing">legacy run: transcript was not retained</span>'
    )
    errors = int(summary.get("n_errors") or 0)
    status_label = "Готово" if errors == 0 else f"{errors} ошибок"
    transcript_data: dict[str, Any] = {}
    if transcript.is_file():
        try:
            transcript_data = json.loads(transcript.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            transcript_data = {}
    chat_html = _render_transcript_chat(transcript_data, row.get("cases", []))
    report_html = (
        render_markdown(report.read_text(encoding="utf-8"))
        if report.is_file() else '<p class="muted">Отчёт отсутствует.</p>'
    )
    card_path.write_text(f"""<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(str(row.get('model', 'unknown')))} · DocBench</title>
<style>
:root{{--bg:#0b1020;--panel:#131b31;--panel2:#192341;--text:#f6f8ff;--muted:#9aa7c3;--line:#2b3858;--accent:#79a8ff;--good:#57d6a0;--bad:#ff7d92;--warn:#ffd27a}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 10% 0%,#1b2b5b 0,transparent 34rem),var(--bg);color:var(--text);font:15px/1.55 Inter,ui-sans-serif,system-ui,sans-serif}}main{{max-width:1050px;margin:0 auto;padding:28px 20px 64px}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:42px}}.back{{font-weight:650}}.eyebrow{{color:var(--muted);font-size:12px;letter-spacing:.14em;text-transform:uppercase}}h1{{font-size:clamp(2rem,5vw,3.8rem);line-height:1.05;letter-spacing:-.05em;margin:8px 0 16px}}.lead{{color:var(--muted);max-width:700px}}.hero{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin-bottom:28px}}.status{{border:1px solid var(--line);border-radius:999px;padding:8px 13px;background:#15223d;color:var(--good);white-space:nowrap;font-weight:700}}.status.bad{{color:var(--bad)}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0 28px}}.metric,.panel{{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:0 16px 45px #05081555}}.metric small{{display:block;color:var(--muted);font-size:12px;margin-bottom:8px}}.metric strong{{font-size:1.35rem;letter-spacing:-.03em}}.panel{{margin-top:16px}}.panel h2{{font-size:1rem;margin:0 0 14px}}pre{{white-space:pre-wrap;overflow:auto;margin:0;background:#0a0f1d;border:1px solid #273451;border-radius:12px;padding:16px;color:#cad6ef;font-size:12px}}.actions{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}.button{{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:10px;padding:9px 13px;background:#172544;color:var(--text);font-weight:650}}.button:hover{{background:#22365e;text-decoration:none}}.alert{{border:1px solid #704353;background:#2a1829;color:#ffc2cc;border-radius:12px;padding:13px 15px;margin-top:16px}}.muted{{color:var(--muted)}}@media(max-width:760px){{.hero{{display:block}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.top{{margin-bottom:28px}}}}@media(max-width:430px){{main{{padding:20px 14px 44px}}.grid{{grid-template-columns:1fr 1fr;gap:8px}}.metric{{padding:13px}}}}
 .transcript-chat{{display:grid;gap:12px}}.transcript-case{{border:1px solid #2b3858;border-radius:12px;background:#0f172a;padding:10px 13px}}.transcript-case>summary{{cursor:pointer;display:flex;justify-content:space-between;gap:12px}}.chat-status,.attempt-meta{{color:var(--muted);font-size:12px}}.attempt{{border-left:2px solid #30476f;margin:12px 0 4px;padding-left:12px}}.attempt-label,.chat-role{{color:#9fb3d9;font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:750;margin:9px 0 5px}}.chat-message{{border:1px solid #2b3858;border-radius:12px;padding:12px 14px;margin:9px 0;overflow:auto}}.chat-message.user{{background:#172c48;border-color:#315685}}.chat-message.assistant{{background:#17283a;border-color:#31616a}}.chat-message.system{{background:#121a2a}}.chat-message p:first-child{{margin-top:0}}.chat-message p:last-child{{margin-bottom:0}}.thinking{{margin-top:10px;border:1px dashed #6d5b2b;border-radius:9px;background:#201c13;padding:8px 11px;color:#cbbd94}}.thinking summary{{cursor:pointer;color:#e5ce7c;font-size:12px;font-weight:700}}.md-code,.chat-message pre{{font-size:12px;line-height:1.5}}.md-table{{border-collapse:collapse;width:100%;font-size:13px}}.md-table th,.md-table td{{border:1px solid #2b3858;padding:7px 9px;text-align:left;vertical-align:top}}.md-table th{{background:#172544;color:#c6d6f3}}.md-table td{{color:#dbe5f9}}.report-preview{{color:#dbe5f9}}
</style>
<body><main><div class=top><a class=back href="{html.escape(_href(card_path, leaderboard_path))}">← Вернуться к рейтингу</a><span class=eyebrow>DocBench · run detail</span></div>
<section class=hero><div><div class=eyebrow>{html.escape(str(row.get('provider_label') or row.get('provider') or 'provider'))} · {html.escape(str(row.get('benchmark') or 'benchmark'))}</div><h1>{html.escape(str(row.get('model', 'unknown')))}</h1><p class=lead>Полная карточка прогона с метриками, стоимостью, токенами и сохранённым транскриптом.</p></div><div class="status{' bad' if errors else ''}">{html.escape(status_label)}</div></section>
<section class=grid><div class=metric><small>Pass rate</small><strong>{_percent(summary.get('case_pass_rate'))}</strong></div><div class=metric><small>F1</small><strong>{_percent(summary.get('finding_f1') or summary.get('extraction_f1'))}</strong></div><div class=metric><small>Стоимость</small><strong>{_rub(summary.get('total_cost_rub'))}</strong></div><div class=metric><small>Время</small><strong>{_seconds(_wall_time(row))}</strong></div></section>
<div class=actions>{transcript_link}<a class=button href="{html.escape(_href(card_path, result_path))}">results.json ↗</a><a class=button href="{html.escape(_href(card_path, report))}">report.md ↗</a></div>
{response_contract.replace('<p>', '<div class=alert>').replace('</p>', '</div>')}
<section class=panel><h2>Полный транскрипт</h2><p class=muted>Сообщения отображаются как чат; системные инструкции и thinking свернуты по умолчанию.</p>{chat_html}</section>
<section class="panel report-preview"><h2>Отчёт</h2>{report_html}</section>
<section class=panel><h2>Детали и ресурсы</h2><pre>{html.escape(json.dumps(metrics, ensure_ascii=False, indent=2))}</pre></section>
<section class=panel><h2>Метаданные запуска</h2><pre>{html.escape(json.dumps(meta, ensure_ascii=False, indent=2))}</pre></section>
</main></body></html>
""", encoding="utf-8")


def _score(value: Any) -> str:
    return "—" if value is None else f"{float(value):.4f}"


def _percent(value: Any) -> str:
    return "—" if value is None else f"{float(value) * 100:.1f}%"


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
        "<div class=table-shell><table><thead><tr><th>Модель</th><th>Кейсы</th><th>Pass rate</th><th>Ошибки</th><th>F1</th>"
        "<th>Стоимость (Cost, RUB)</th><th>₽ / кейс</th><th>Вход</th><th>Выход</th>"
        "<th>Кэш</th><th>Reasoning</th><th>p50</th><th>Время</th>"
        "<th>Транскрипт</th></tr></thead><tbody>"
    ]
    for row in sorted(rows, key=lambda x: (x["summary"].get("case_pass_rate") or -1), reverse=True):
        result_path = Path(row["_path"])
        card = result_path.with_name("run.html")
        _run_card(row, card, output)
        transcript = result_path.with_name("transcript.json")
        summary = row["summary"]
        errors = int(summary.get("n_errors") or 0)
        status = "ok" if errors == 0 else "error"
        parts.append(
            "<tr class=run-row data-href=\"%s\" data-model=\"%s\" data-errors=\"%s\" tabindex=\"0\" role=\"link\"><td>"
            "<div class=model-cell><span class=model-dot></span><span class=model-name>%s</span></div></td><td>%s</td>"
            "<td><strong class=rate>%s</strong></td><td><span class=badge-%s>%s</span></td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(_href(output, card)), html.escape(str(row.get("model", "")).lower()), errors,
                html.escape(str(row.get("model", ""))), summary.get("n_cases", "—"),
                _percent(summary.get("case_pass_rate")), status, errors or "OK",
                _percent(summary.get("finding_f1") or summary.get("extraction_f1")),
                _rub(summary.get("total_cost_rub")), _rub(summary.get("cost_per_case_rub")),
                _count(_tokens(row, "input_tokens")), _count(_tokens(row, "output_tokens")),
                _count(_tokens(row, "cache_input_tokens")), _count(_tokens(row, "reasoning_tokens")),
                _seconds(summary.get("latency_p50_s")), _seconds(_wall_time(row)),
                "есть" if transcript.is_file() else "<!-- legacy / no -->нет",
            )
        )
    return "".join(parts) + "</tbody></table></div>"


def _overall_table(rows: list[dict[str, Any]]) -> str:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model[str(row.get("model", ""))].append(row)
    parts = [
        "<div class=table-shell><table><thead><tr><th>Модель</th><th>Покрытие</th><th>Weighted pass rate</th><th>Статус</th>"
        "<th>Стоимость (Cost, RUB)</th><th>₽ / кейс</th><th>Вход</th><th>Выход</th>"
        "<th>Кэш</th><th>Reasoning</th><th>p50</th><th>Время</th>"
        "</tr></thead><tbody>"
    ]
    aggregates = []
    for model, model_rows in by_model.items():
        covered = sum(int(r["summary"].get("n_cases") or 0) for r in model_rows)
        passed = sum((r["summary"].get("case_pass_rate") or 0) * (r["summary"].get("n_cases") or 0) for r in model_rows)
        complete = (
            covered == STANDARD_CASE_COUNT
            and {r["_cases_key"] for r in model_rows} == set(STANDARD_SUITES)
            and all((r["summary"].get("n_errors") or 0) == 0 for r in model_rows)
        )
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
        parts.append("<tr><td><strong>%s</strong></td><td>%s / %s</td><td><strong>%s</strong></td><td>%s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            html.escape(model), covered, STANDARD_CASE_COUNT, _percent(rate), "<span class=badge-ok>готово</span>" if complete else "<span class=badge-warn>частично</span>",
            _rub(total_cost), _rub(total_cost / covered if total_cost is not None and covered else None),
            _count(token_totals["input_tokens"]), _count(token_totals["output_tokens"]),
            _count(token_totals["cache_input_tokens"]), _count(token_totals["reasoning_tokens"]),
            _seconds(latency_p50), _seconds(wall_time),
        ))
    return "".join(parts) + "</tbody></table></div>"


def write_leaderboard(runs_dir: Path, output: Path) -> dict[str, Any]:
    """Generate a local HTML index and one clickable card per saved run."""
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_runs(runs_dir)
    standard = _newest_per_model_suite([r for r in rows if r["_cases_key"] in STANDARD_SUITES])
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in standard:
        groups[row["_cases_key"]].append(row)
    model_count = len({str(row.get("model", "")) for row in standard})
    total_cases = sum(int(row["summary"].get("n_cases") or 0) for row in standard)
    total_errors = sum(int(row["summary"].get("n_errors") or 0) for row in standard)
    sections = ["<section class=section><div class=section-heading><div><div class=eyebrow>Сводный рейтинг</div><h2>Все стандартные suite</h2></div></div>", _overall_table(standard), "</section>"]
    for key, (name, expected) in STANDARD_SUITES.items():
        sections.extend([f'<section class="section suite-section" data-suite="{html.escape(key)}"><div class=section-heading><div><div class=eyebrow>{expected} кейсов</div><h2>{html.escape(name)}</h2></div><span class=suite-count>{len(groups[key])} моделей</span></div>', _table(groups[key], output), "</section>"])
    output.write_text(f"""<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DocBench · рейтинг моделей</title>
<style>
:root{{--bg:#0b1020;--panel:#131b31;--panel2:#192341;--text:#f6f8ff;--muted:#9aa7c3;--line:#2b3858;--accent:#79a8ff;--accent2:#a78bfa;--good:#57d6a0;--bad:#ff7d92;--warn:#ffd27a}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 8% -4%,#253c7b 0,transparent 34rem),radial-gradient(circle at 94% 0%,#30215e 0,transparent 28rem),var(--bg);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}main{{max-width:1440px;margin:0 auto;padding:28px 28px 80px}}.topbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:56px}}.brand{{display:flex;align-items:center;gap:11px;font-weight:800;letter-spacing:-.02em}}.brand-mark{{width:30px;height:30px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 0 30px #7da7ff66;position:relative}}.brand-mark:after{{content:"";position:absolute;inset:7px;border:2px solid #fff;border-radius:5px;opacity:.9}}.top-meta{{color:var(--muted);font-size:12px}}.hero{{display:flex;justify-content:space-between;gap:28px;align-items:flex-end;margin-bottom:30px}}.eyebrow{{font-size:11px;color:var(--muted);letter-spacing:.14em;text-transform:uppercase;font-weight:750}}h1{{font-size:clamp(2.7rem,7vw,5.8rem);line-height:.95;letter-spacing:-.075em;margin:11px 0 17px;max-width:900px}}.hero-copy{{color:var(--muted);font-size:16px;max-width:680px;margin:0}}.hero-copy strong{{color:var(--text)}}.hero-mark{{font-size:11px;color:#c8d4ef;background:#162544;border:1px solid var(--line);padding:9px 12px;border-radius:999px;white-space:nowrap}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:30px 0 38px}}.stat{{background:linear-gradient(145deg,#1d2b4b,#121a2e);border:1px solid var(--line);border-radius:17px;padding:18px 19px;box-shadow:0 18px 50px #05081555}}.stat small{{display:block;color:var(--muted);font-size:12px;margin-bottom:7px}}.stat strong{{display:block;font-size:1.7rem;letter-spacing:-.045em}}.stat .hint{{color:var(--muted);font-size:12px;margin-top:4px}}.toolbar{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:30px;padding:12px;border:1px solid var(--line);border-radius:14px;background:#111a2eaa;backdrop-filter:blur(12px)}}.toolbar label{{color:var(--muted);font-size:12px;font-weight:650}}input,select{{appearance:none;border:1px solid var(--line);border-radius:10px;background:#0e172b;color:var(--text);padding:10px 12px;font:inherit;min-height:40px}}input{{min-width:250px}}input:focus,select:focus{{outline:2px solid #7da7ff66;outline-offset:1px}}.section{{margin-top:34px}}.section-heading{{display:flex;align-items:end;justify-content:space-between;gap:16px;margin:0 0 14px}}h2{{font-size:1.55rem;letter-spacing:-.04em;margin:5px 0 0}}.suite-count{{color:var(--muted);font-size:12px;background:#141f37;border:1px solid var(--line);padding:6px 9px;border-radius:999px}}.table-shell{{overflow:auto;border:1px solid var(--line);border-radius:16px;background:#10182b;box-shadow:0 18px 50px #05081544}}table{{border-collapse:collapse;width:100%;min-width:1120px}}th,td{{padding:13px 14px;text-align:left;border-bottom:1px solid #25324d;white-space:nowrap}}th{{color:#8493b2;font-size:11px;letter-spacing:.08em;text-transform:uppercase;background:#141e35;position:sticky;top:0;z-index:1}}tbody tr:last-child td{{border-bottom:0}}.run-row{{cursor:pointer;transition:background .18s,transform .18s}}.run-row:hover,.run-row:focus{{background:#192847;outline:none}}.run-row:hover{{box-shadow:inset 3px 0 0 var(--accent)}}.model-cell{{display:flex;align-items:center;gap:9px;min-width:215px}}.model-dot{{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 0 13px #7da7ffaa;flex:none}}.model-name{{font-weight:700;color:#edf2ff}}.rate{{font-size:15px;color:#e5edff}}.badge-ok,.badge-error,.badge-warn{{display:inline-flex;align-items:center;border-radius:999px;padding:4px 8px;font-size:11px;font-weight:750}}.badge-ok{{background:#12372f;color:var(--good)}}.badge-error{{background:#3c1a2a;color:var(--bad)}}.badge-warn{{background:#3c2d18;color:var(--warn)}}.note{{color:var(--muted);font-size:12px;margin-top:12px}}.empty{{display:none;padding:28px;color:var(--muted);text-align:center}}.footer{{margin-top:54px;color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:16px;border-top:1px solid var(--line);padding-top:18px}}@media(max-width:800px){{main{{padding:20px 14px 56px}}.hero{{display:block}}.hero-mark{{display:inline-block;margin-top:20px}}.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.topbar{{margin-bottom:38px}}}}@media(max-width:480px){{.stats{{gap:8px}}.stat{{padding:14px}}.stat strong{{font-size:1.35rem}}input{{min-width:0;width:100%}}.toolbar label{{width:100%}}.footer{{display:block}}}}
</style>
<body><main><header class=topbar><div class=brand><span class=brand-mark></span><span>DocBench</span></div><div class=top-meta>Russian document benchmark · {html.escape(datetime.now().strftime('%d.%m.%Y %H:%M'))}</div></header>
<section class=hero><div><div class=eyebrow>Benchmark intelligence</div><h1>Рейтинг моделей<br><span style="color:var(--accent)">для документов</span></h1><p class=hero-copy>Сравнение качества, скорости, стоимости и полноты ответов. <strong>Кликните по строке</strong>, чтобы открыть полный транскрипт и детали прогона.</p></div><span class=hero-mark>seed datasets · auditable runs</span></section>
<section class=stats><div class=stat><small>Моделей</small><strong>{model_count}</strong><div class=hint>в текущем срезе</div></div><div class=stat><small>Прогонов</small><strong>{len(standard)}</strong><div class=hint>по всем suite</div></div><div class=stat><small>Кейсов</small><strong>{total_cases:,}</strong><div class=hint>{total_errors} с ошибкой</div></div><div class=stat><small>Полные транскрипты</small><strong>{sum(1 for row in standard if (Path(row['_path']).with_name('transcript.json')).is_file())}/{len(standard)}</strong><div class=hint>сохранены рядом</div></div></section>
<div class=toolbar><label for=model-filter>Фильтр</label><input id=model-filter type=search placeholder="Найти модель…"><label for=suite-filter>Suite</label><select id=suite-filter><option value=all>Все suite</option>{''.join(f'<option value="{html.escape(key)}">{html.escape(name)}</option>' for key,(name,_) in STANDARD_SUITES.items())}</select><span class=note id=visible-count></span></div>
{''.join(sections)}
<footer class=footer><span>Generated {html.escape(datetime.now().isoformat(timespec='seconds'))}</span><span>Standard rank requires all {STANDARD_CASE_COUNT} cases · prices in RUB</span></footer>
</main><script>
const rows=[...document.querySelectorAll('.run-row')], filter=document.querySelector('#model-filter'), suite=document.querySelector('#suite-filter'), count=document.querySelector('#visible-count');
function applyFilter(){{const q=(filter.value||'').toLowerCase().trim(), s=suite.value;let shown=0;document.querySelectorAll('.suite-section').forEach(section=>{{const suiteOk=s==='all'||section.dataset.suite===s;let sectionShown=0;section.querySelectorAll('.run-row').forEach(row=>{{const ok=suiteOk&&(!q||row.dataset.model.includes(q));row.style.display=ok?'':'none';if(ok){{shown++;sectionShown++}}}});section.style.display=sectionShown?'':'none'}});count.textContent=shown+' строк'}}
function sortTable(table, header, index){{const body=table.tBodies[0], direction=header.dataset.dir==='asc'?'desc':'asc';table.querySelectorAll('thead th').forEach(th=>delete th.dataset.dir);header.dataset.dir=direction;const items=[...body.rows];items.sort((a,b)=>{{const av=a.cells[index]?.textContent.trim()||'',bv=b.cells[index]?.textContent.trim()||'';const an=Number(av.replace(/[^0-9.-]/g,'')),bn=Number(bv.replace(/[^0-9.-]/g,''));let result=Number.isFinite(an)&&Number.isFinite(bn)?an-bn:av.localeCompare(bv,'ru',{{numeric:true,sensitivity:'base'}});return direction==='asc'?result:-result}});items.forEach(row=>body.appendChild(row))}}
document.querySelectorAll('table').forEach(table=>table.querySelectorAll('thead th').forEach((header,index)=>{{header.classList.add('sortable');header.tabIndex=0;header.setAttribute('role','button');header.addEventListener('click',()=>sortTable(table,header,index));header.addEventListener('keydown',event=>{{if(event.key==='Enter'||event.key===' '){{event.preventDefault();sortTable(table,header,index)}}}})}}));
filter.addEventListener('input',applyFilter);suite.addEventListener('change',applyFilter);rows.forEach(row=>{{row.addEventListener('click',()=>location.href=row.dataset.href);row.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();location.href=row.dataset.href}}}})}});applyFilter();
</script></body></html>""", encoding="utf-8")
    return {"runs": len(rows), "out": str(output)}


def publish_pages(campaign_dir: Path, output: Path) -> dict[str, Any]:
    """Copy one finished campaign and render a self-contained GitHub Pages site."""
    campaign_dir = campaign_dir.resolve()
    if not campaign_dir.is_dir():
        raise FileNotFoundError(f"campaign directory not found: {campaign_dir}")
    target = output / "runs" / campaign_dir.name
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(campaign_dir, target)
    _sanitize_public_results(target)
    result = write_leaderboard(output / "runs", output / "index.html")
    (output / ".nojekyll").touch()
    return {**result, "campaign": str(target)}


def _sanitize_public_results(runs_dir: Path) -> None:
    """Keep public artifacts reproducible without disclosing local filesystem paths."""
    for result_path in runs_dir.glob("**/results.json"):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        changed = False
        for key in ("cases_path", "out_dir"):
            value = result.get(key)
            if isinstance(value, str):
                cleaned = _public_path(value)
                changed = changed or cleaned != value
                result[key] = cleaned
        for case in result.get("cases", []):
            value = case.get("source")
            if isinstance(value, str):
                cleaned = _public_path(value)
                changed = changed or cleaned != value
                case["source"] = cleaned
        if changed:
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def _public_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return value
    parts = path.parts
    if "cases" in parts:
        return Path(*parts[parts.index("cases"):]).as_posix()
    return path.name
