import json

from docbench.leaderboard import write_leaderboard


def _result(model: str, cases_path: str, n_cases: int, rate: float) -> dict:
    return {
        "ts": "2026-08-18T12:00:00+00:00",
        "model": model,
        "summary": {"n_cases": n_cases, "n_errors": 0, "case_pass_rate": rate,
                    "finding_f1": rate, "extraction_f1": None},
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
    assert "data-href" in text
    assert "legacy / no" in text
    assert (runs / "grant" / "run.html").is_file()
    assert "transcript.json" in (runs / "grant" / "run.html").read_text()
