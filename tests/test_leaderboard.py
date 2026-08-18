import json

from docbench.leaderboard import publish_pages, write_leaderboard


def _result(model: str, cases_path: str, n_cases: int, rate: float, *, priced: bool = True) -> dict:
    total_cost = 1.5 if priced else None
    return {
        "ts": "2026-08-18T12:00:00+00:00",
        "model": model,
        "summary": {
            "n_cases": n_cases, "n_errors": 0, "case_pass_rate": rate,
            "finding_f1": rate, "extraction_f1": None,
            "total_cost_rub": total_cost,
            "cost_per_case_rub": total_cost / n_cases if total_cost is not None else None,
            "latency_p50_s": 2.5,
            "wall_time_s": 12.0,
            "tokens": {
                "input_tokens": 100, "output_tokens": 40,
                "cache_input_tokens": 20, "reasoning_tokens": 0,
            },
        },
        "cases_path": cases_path,
    }


def test_leaderboard_generates_clickable_cards_and_marks_legacy(tmp_path):
    runs = tmp_path / "runs"
    for name, path, n, rate, transcript in [
        ("grant", "cases/seed-grant", 10, 0.8, True),
        ("policy", "cases/seed-policy", 2, 1.0, False),
        ("ace", "cases/ace-test", 30, 0.7, True),
    ]:
        out = runs / name
        out.mkdir(parents=True)
        (out / "results.json").write_text(json.dumps(_result("test-model", path, n, rate)))
        (out / "report.md").write_text("report")
        if transcript:
            (out / "transcript.json").write_text("{}")

    index = tmp_path / "leaderboard" / "index.html"
    result = write_leaderboard(runs, index)

    text = index.read_text()
    assert result["runs"] == 3
    assert "Weighted pass rate" in text
    assert "42 / 52" in text
    assert "data-href" in text
    assert "legacy / no" in text
    assert "Cost, RUB" in text
    assert "1.50 ₽" in text
    assert "0.15 ₽" in text
    assert "100" in text
    assert "2.5 s" in text
    assert "12.0 s" in text
    assert (runs / "grant" / "run.html").is_file()
    assert "transcript.json" in (runs / "grant" / "run.html").read_text()


def test_leaderboard_uses_dash_for_unpriced_or_missing_measurements(tmp_path):
    runs = tmp_path / "runs"
    out = runs / "unpriced"
    out.mkdir(parents=True)
    result = _result("unpriced-model", "cases/seed-grant", 10, 0.8, priced=False)
    result["summary"].pop("wall_time_s")
    result["summary"]["tokens"].pop("cache_input_tokens")
    (out / "results.json").write_text(json.dumps(result))
    (out / "report.md").write_text("report")

    index = tmp_path / "leaderboard" / "index.html"
    write_leaderboard(runs, index)

    text = index.read_text()
    assert "0.00 ₽" not in text
    assert "—" in text


def test_publish_pages_copies_campaign_and_renders_relative_artifacts(tmp_path):
    campaign = tmp_path / "campaign"
    run = campaign / "grant" / "test-model"
    run.mkdir(parents=True)
    (run / "results.json").write_text(json.dumps(_result("test-model", "/private/work/cases/seed-grant", 10, 0.8)))
    (run / "report.md").write_text("report")
    (run / "transcript.json").write_text("{}")

    pages = tmp_path / "docs"
    result = publish_pages(campaign, pages)

    assert result["runs"] == 1
    assert (pages / "index.html").is_file()
    assert (pages / ".nojekyll").is_file()
    assert (pages / "runs" / "campaign" / "grant" / "test-model" / "transcript.json").is_file()
    assert "runs/campaign/grant/test-model/run.html" in (pages / "index.html").read_text()
    copied = json.loads((pages / "runs" / "campaign" / "grant" / "test-model" / "results.json").read_text())
    assert copied["cases_path"] == "cases/seed-grant"
