#!/usr/bin/env python3
"""Publish one self-contained, Russian-language supplementary leaderboard."""
from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


SUITES = {
    "grant": ("Грантовые заявки", 10),
    "policy": ("Извлечение правил из русских политик", 12),
    "ace": ("Договоры ACE", 30),
}
TOTAL_CASES = sum(expected for _, expected in SUITES.values())


def _pct(value: object) -> str:
    return "—" if value is None else f"{float(value) * 100:.1f}%"


def _rub(value: object) -> str:
    return "—" if value is None else f"{float(value):.2f} ₽"


def _read_campaign(root: Path) -> list[tuple[str, str, Path, dict]]:
    rows: list[tuple[str, str, Path, dict]] = []
    for path in sorted(root.glob("*/*/results.json")):
        suite, model = path.relative_to(root).parts[:2]
        if suite not in SUITES:
            continue
        rows.append((suite, model, path, json.loads(path.read_text(encoding="utf-8"))))
    return rows


def publish(campaign_dir: Path, output: Path) -> None:
    rows = _read_campaign(campaign_dir)
    if not rows:
        raise ValueError(f"no Russian results under {campaign_dir}")
    by_model: dict[str, dict[str, tuple[Path, dict]]] = {}
    for suite, model, path, result in rows:
        by_model.setdefault(model, {})[suite] = (path, result)
    output.mkdir(parents=True, exist_ok=True)
    runs_out = output / "runs"
    if runs_out.exists():
        shutil.rmtree(runs_out)
    for suite, model, path, _result in rows:
        shutil.copytree(path.parent, runs_out / suite / model)

    body = []
    for model, suites in sorted(by_model.items()):
        covered = sum(int(data.get("n_cases") or 0) for _, data in suites.values())
        rates = [data.get("summary", {}).get("case_pass_rate") for _, data in suites.values()]
        rate = sum(rates) / len(rates) if rates and all(value is not None for value in rates) else None
        errors = sum(int(data.get("summary", {}).get("n_errors") or 0) for _, data in suites.values())
        costs = [data.get("summary", {}).get("total_cost_rub") for _, data in suites.values()]
        cost = sum(costs) if all(value is not None for value in costs) else None
        status = "полный" if covered == TOTAL_CASES and len(suites) == len(SUITES) and not errors else "частичный"
        cells = [
            f"<td><strong>{html.escape(model)}</strong></td>", f"<td>{covered} / {TOTAL_CASES}</td>",
            f"<td>{_pct(rate)}</td>", f"<td>{html.escape(status)}</td>", f"<td>{_rub(cost)}</td>",
        ]
        for suite in SUITES:
            item = suites.get(suite)
            if item is None:
                cells.append("<td>—</td>")
                continue
            path, data = item
            summary = data.get("summary", {})
            href = f"runs/{suite}/{model}/transcript.json"
            cells.append(f'<td><a href="{html.escape(href)}">{_pct(summary.get("case_pass_rate"))}</a></td>')
        body.append("<tr>" + "".join(cells) + "</tr>")

    generated = datetime.now(timezone.utc).isoformat()
    output.joinpath("index.html").write_text(f"""<!doctype html>
<html lang=\"ru\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>DocBench — русский дополнительный leaderboard</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 18px;color:#172033}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #d7deea;text-align:left}}th{{background:#f3f6fb}}a{{color:#175cd3}}.note{{color:#52627a;line-height:1.5}}</style>
<h1>Русскоязычный дополнительный leaderboard</h1>
<p class=\"note\">Отдельный 52-case срез: 10 переведённых grant, 12 нативных русских policy и 30 переведённых ACE. Он не смешивается с основным рейтингом. Число в suite — строгий pass rate; ссылка открывает полный транскрипт модели.</p>
<table><thead><tr><th>Модель</th><th>Покрытие</th><th>Среднее по suite</th><th>Статус</th><th>Стоимость</th><th>Grant</th><th>Policy</th><th>ACE</th></tr></thead><tbody>{''.join(body)}</tbody></table>
<p class=\"note\">Сгенерировано {html.escape(generated)} из сохранённых results.json и transcript.json.</p>
</html>""", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    publish(args.campaign_dir, args.out)
