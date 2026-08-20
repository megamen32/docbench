import json

from docbench.leaderboard import _render_message, _render_transcript_chat, publish_pages, render_markdown, write_leaderboard
from docbench.run import reprice_saved_results


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
    card = (runs / "grant" / "run.html").read_text()
    assert "transcript.json" in card
    assert '<details class="transcript-optin">' in card


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


def test_run_card_renders_safe_markdown_and_collapsed_thinking():
    rendered = render_markdown("# Title\n\n- **bold** and " + chr(96) + "code" + chr(96) + "\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n<script>alert(1)</script>")
    assert "<h1>Title</h1>" in rendered
    assert "<strong>bold</strong>" in rendered
    assert "<div class=md-table-wrap><table class=md-table>" in rendered
    status = render_markdown("- ✅ `grant_00001__corr_missing_registration` _(remove_document: removed 'registration_cert')_ — reject")
    assert "grant_00001__corr_missing_registration" in status
    assert "✅" in status
    assert "<code>grant_00001__corr_missing_registration</code>" in status
    assert "<em>(remove_document: removed 'registration_cert')</em>" in status
    assert "md-status-icon" in status
    rich = render_markdown("_italic_ __bold__ ~~strike~~")
    assert "<em>italic</em>" in rich
    assert "<strong>bold</strong>" in rich
    assert "<del>strike</del>" in rich
    assert "&lt;script&gt;" in rendered
    visible, thinking = _render_message("<think>private reasoning</think>**final**")
    assert "<strong>final</strong>" in visible
    assert "private reasoning" in thinking
    assert "<details" in thinking


def test_transcript_chat_is_opt_in_and_cases_start_collapsed():
    transcript = {"cases": [{"case_id": "case-1", "attempts": [{
        "attempt": 1, "messages": [{"role": "user", "content": "hello"}],
        "response_text": "world", "usage": {"total_tokens": 2},
    }]}]}
    rendered = _render_transcript_chat(transcript, [{"case_id": "case-1", "ok": True}])
    assert '<details class="transcript-case">' in rendered
    assert '<details class="transcript-case" open>' not in rendered
    assert "case-status-icon" in rendered
    assert "✅" in rendered


def test_reprice_saved_results_uses_pinned_catalog_rates(tmp_path):
    run = tmp_path / "runs" / "terra"
    run.mkdir(parents=True)
    data = _result("omniroute-cx-gpt-5.6-terra-medium", "cases/seed-grant", 1, 1.0, priced=False)
    data["cases"] = [{
        "case_id": "one", "ok": True, "finding_precision": 1.0,
        "usage": {"input_tokens": 1000, "output_tokens": 500,
                  "cache_read_input_tokens": 100, "cache_write_input_tokens": 0,
                  "uncached_input_tokens": 900, "reasoning_tokens": 0},
        "cost_rub": None,
    }]
    (run / "results.json").write_text(json.dumps(data))
    changed = reprice_saved_results(tmp_path / "runs")
    assert changed["changed"]
    repriced = json.loads((run / "results.json").read_text())
    assert repriced["cases"][0]["cost_rub"] == 0.431588
    assert repriced["summary"]["total_cost_rub"] == 0.431588
