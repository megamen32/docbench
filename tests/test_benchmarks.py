"""Offline end-to-end: canned oracle-perfect reply flows through parse+score
and through the full run orchestrator via a pre-seeded response cache."""
import json
import shutil
from datetime import datetime
from pathlib import Path

from docbench.benchmarks.base import load_case
from docbench.benchmarks.conformance import ConformanceBenchmark
from docbench.benchmarks.rule_extraction import RuleExtractionBenchmark
from docbench.benchmarks.base import load_ruleset
from docbench.oracle import flatten_case, gold_for
from docbench.run import rescore_saved_results

REPO = Path(__file__).resolve().parent.parent


def test_complete_cache_cold_run_blocks_duplicate_online_call(monkeypatch, tmp_path):
    import docbench.run as R

    existing = tmp_path / "existing" / "grant" / "test-model"
    existing.mkdir(parents=True)
    (existing / "results.json").write_text(json.dumps({
        "model": "test-model",
        "benchmark": "conformance",
        "cases_path": "datasets/russian/grant/cases",
        "locale": "ru",
        "dataset_version": "russian-grant-v1",
        "cache_mode": "bypass",
        "n_cases": 10,
        "summary": {"n_errors": 0},
    }), encoding="utf-8")
    monkeypatch.setattr(R, "RUNS_DIR", tmp_path)

    assert R._find_complete_online_run(
        model="test-model", benchmark="conformance",
        cases_path=REPO / "datasets/russian/grant/cases", locale="ru",
        dataset_version="russian-grant-v1", expected_cases=10,
    ) == existing


def test_repeat_label_requires_explicit_repeat_authorization(tmp_path):
    import docbench.run as R

    try:
        R.run_benchmark(
            "conformance", "not-reached", tmp_path / "missing.yaml",
            allow_repeat=True,
        )
    except ValueError as exc:
        assert str(exc) == "repeat_label is required when allow_repeat=True"
    else:
        raise AssertionError("missing repeat label must be rejected before provider setup")


def _perfect_reply(bench, case, gold):
    findings = [
        {"rule_id": f.rule_id, "status": f.status,
         "expected": f.expected, "observed": f.observed,
         "evidence": (f.evidence.model_dump(exclude_none=True) if f.evidence else None)}
        for f in gold_for(case, bench.ruleset)[0]
    ]
    return json.dumps({
        "extracted": {k: flatten_case(case).get(k) for k in bench.canonical_fields},
        "findings": findings,
        "disposition": gold_for(case, bench.ruleset)[1],
    }, ensure_ascii=False)


def test_conformance_parse_and_score_perfect(valid_case, ruleset):
    bench = ConformanceBenchmark(ruleset)
    gold = bench.gold_for(valid_case)
    reply = _perfect_reply(bench, valid_case, gold)
    payload, err = bench.parse(reply, valid_case)
    assert err is None
    scores = bench.score(payload, gold, valid_case)
    assert scores["ok"] is True
    assert scores["finding_f1"] == 1.0
    assert scores["extraction_f1"] == 1.0
    assert scores["false_accept"] is False and scores["false_reject"] is False


def test_conformance_parse_think_wrapped(valid_case, ruleset):
    bench = ConformanceBenchmark(ruleset)
    gold = bench.gold_for(valid_case)
    reply = "<think>let me check each rule…</think>\n" + _perfect_reply(bench, valid_case, gold)
    payload, err = bench.parse(reply, valid_case)
    assert payload is not None
    assert bench.score(payload, gold, valid_case)["ok"] is True


def test_conformance_false_accept_detected(valid_case, ruleset):
    bench = ConformanceBenchmark(ruleset)
    gold = bench.gold_for(valid_case)
    # model claims everything is fine on a packet gold says needs_correction
    bad_case = valid_case.model_copy(deep=True)
    bad_case.documents["application_form"].fields["signature_present"] = False
    gold_bad = bench.gold_for(bad_case)
    perfect_on_valid = _perfect_reply(bench, valid_case, gold)
    payload, _ = bench.parse(perfect_on_valid, bad_case)
    scores = bench.score(payload, gold_bad, bad_case)
    assert scores["false_accept"] is True
    assert scores["ok"] is False


def test_rule_extraction_parse_and_score(tmp_path):
    case = load_case(REPO / "cases" / "seed-policy" / "policy_foundation_v2.yaml")
    bench = RuleExtractionBenchmark()
    gold = bench.gold_for(case)
    reply = json.dumps({"ruleset_id": "northstar-v2.4", "rules": [
        {"description": r.description, "severity": r.severity, "category": r.category,
         "condition": r.condition.model_dump(exclude_none=True)}
        for r in gold["rules"]
    ]}, ensure_ascii=False)
    payload, err = bench.parse(reply, case)
    assert err is None
    scores = bench.score(payload, gold, case)
    assert scores["f1"] == 1.0 and scores["ok"] is True


def test_russian_locale_emits_russian_prompt_contract(valid_case, ruleset):
    conformance = ConformanceBenchmark(ruleset, locale="ru")
    conformance_messages = conformance.messages(valid_case, conformance.gold_for(valid_case))
    assert conformance_messages[0]["content"].startswith("Вы —")
    assert "НАБОР ПРАВИЛ" in conformance_messages[1]["content"]

    policy_case = load_case(REPO / "cases" / "seed-policy" / "policy_foundation_v2.yaml")
    extraction = RuleExtractionBenchmark(locale="ru")
    extraction_messages = extraction.messages(policy_case, extraction.gold_for(policy_case))
    assert extraction_messages[0]["content"].startswith("Вы —")
    assert "РЕЕСТР КАНОНИЧЕСКИХ ПОЛЕЙ" in extraction_messages[1]["content"]


def test_rescore_saved_rule_run_uses_current_presence_normalization(tmp_path):
    cases = tmp_path / "cases"
    cases.mkdir()
    case_path = cases / "policy.yaml"
    case_path.write_text("""
id: policy_presence
benchmark: rule_extraction
canonical_fields: [documents.venue_consent.present]
policy_document: "Для мероприятия требуется согласие площадки."
expected_rules:
  - {id: P1, description: Согласие площадки, severity: major, category: documents, condition: {field: documents.venue_consent.present, op: exists}}
""", encoding="utf-8")
    run = tmp_path / "runs" / "policy" / "model"
    run.mkdir(parents=True)
    result = {
        "benchmark": "rule_extraction", "model": "model", "cases_path": str(cases),
        "cases": [{"case_id": "policy_presence", "finding_f1": 0.0, "ok": False,
                   "cost_rub": 0.1, "latency_s": 1.0,
                   "usage": {"input_tokens": 1, "output_tokens": 1}}],
    }
    (run / "results.json").write_text(json.dumps(result), encoding="utf-8")
    response = json.dumps({"rules": [{
        "description": "Согласие площадки", "severity": "major", "category": "documents",
        "condition": {"field": "documents.venue_consent.present", "op": "exists", "value": True},
    }]}, ensure_ascii=False)
    (run / "transcript.json").write_text(json.dumps({"cases": [{
        "case_id": "policy_presence", "attempts": [{"response_text": response}],
    }]}), encoding="utf-8")

    changed = rescore_saved_results(tmp_path / "runs")
    assert changed["changed"]
    rescored = json.loads((run / "results.json").read_text())
    assert rescored["cases"][0]["finding_f1"] == 1.0
    assert rescored["cases"][0]["ok"] is True


def test_full_offline_run_with_seeded_cache(tmp_path, valid_case, ruleset, monkeypatch):
    import docbench.run as R

    bench = ConformanceBenchmark(ruleset)
    gold = bench.gold_for(valid_case)
    reply = _perfect_reply(bench, valid_case, gold)

    cache = tmp_path / "cache"
    runner = R.OpenAICompatRunner.__new__(R.OpenAICompatRunner)
    spec = type("S", (), {"key": "fake", "alias": "fake", "price_in": 1.0, "price_out": 2.0,
                          "price_source": "assumed-test", "provider": "fake",
                          "provider_label": "Fake", "quantization": None,
                          "request_extra": {}, "effort_levels": {},
                          "effort_default": "provider-default",
                          "effort_extra": lambda self, effort=None: {}})()
    runner.__dict__.update(spec=spec, model_key="fake", alias="fake", base_url="http://x",
                           _api_key="k", timeout=1, max_retries=1, offline=True, cache_dir=cache)
    case_file = tmp_path / "c.yaml"
    import yaml
    case_file.write_text(yaml.safe_dump(valid_case.model_dump(exclude_none=True),
                                        allow_unicode=True, sort_keys=False), encoding="utf-8")
    ruleset_dir = tmp_path / "rulesets"
    ruleset_dir.mkdir()
    shutil.copy(REPO / "rulesets" / "seed-grant-2026.1.yaml", ruleset_dir)
    cache.mkdir(parents=True, exist_ok=True)
    # Seed the serialized case's request, exactly as run_benchmark will load it.
    run_case = load_case(case_file)
    run_gold = bench.gold_for(run_case)
    key = runner._cache_key(bench.messages(run_case, run_gold), 0.0, 8192)
    runner._cache_put(key, type("C", (), {"text": reply, "usage": {"prompt_tokens": 10, "completion_tokens": 10},
                                          "latency_s": 0.1, "cost_usd": 0.5,
                                          "cost_is_estimate": True, "model": "fake",
                                          "cache_hit": False})())

    # point the orchestrator at our runner factory state
    monkeypatch.setattr(R, "CACHE_DIR", cache)
    monkeypatch.setattr(R, "resolve_model", lambda k, allow_missing_key=False: spec)
    monkeypatch.setattr(R, "OpenAICompatRunner", lambda s, cache_dir=None, offline=False:
                        runner)

    res = R.run_benchmark("conformance", "fake", case_file,
                          ruleset_dir=ruleset_dir, out_dir=tmp_path / "out",
                          dataset_version="offline-canary-v1",
                          fx_snapshot={"usd_rub": 80.0, "date": "2026-08-18", "source": "explicit"})
    assert res["summary"]["case_pass_rate"] == 1.0
    assert res["summary"]["finding_f1"] == 1.0
    assert res["dataset_version"] == "offline-canary-v1"
    assert res["fx_snapshot"]["usd_rub"] == 80.0
    assert res["cases"][0]["cost_rub"] == 40.0
    assert res["summary"]["total_cost_rub"] == 40.0
    assert res["wall_time_s"] >= 0
    assert datetime.fromisoformat(res["started_at"])
    assert datetime.fromisoformat(res["finished_at"])
    transcript = json.loads((tmp_path / "out" / "transcript.json").read_text(encoding="utf-8"))
    assert res["artifacts"]["transcript"] == "transcript.json"
    assert transcript["cases"][0]["attempts"][0]["response_text"] == reply
    manifest = res["reproducibility"]
    assert manifest["schema_version"] == 1
    assert len(manifest["code"]["git_revision"]) == 40
    assert len(manifest["inputs"]["cases"]["sha256"]) == 64
    assert manifest["inputs"]["rulesets"]["files"] == [{
        "path": str(ruleset_dir / "seed-grant-2026.1.yaml"),
        "sha256": __import__("hashlib").sha256(
            (REPO / "rulesets" / "seed-grant-2026.1.yaml").read_bytes()
        ).hexdigest(),
    }]
    attempt = transcript["cases"][0]["attempts"][0]
    assert attempt["messages_sha256"] == R._canonical_sha256(attempt["messages"])
    assert transcript["run"]["reproducibility"] == manifest


def test_campaign_uses_one_cbr_snapshot_and_profile_versions(monkeypatch, tmp_path):
    import docbench.run as R

    cbr = {"usd_rub": 81.25, "date": "2026-08-18", "source": "CBR"}
    calls = []
    monkeypatch.setattr(R, "fetch_cbr_usd_rub", lambda: cbr)

    def fake_run(bench, model, cases, **kwargs):
        calls.append((bench, model, cases, kwargs))
        return {"model": model, "benchmark": bench, "out_dir": str(kwargs["out_dir"])}

    monkeypatch.setattr(R, "run_benchmark", fake_run)
    results = R.run_campaign(["fake-model"], ["policy"], out_dir=tmp_path / "campaign")

    assert len(results) == 1
    bench, model, cases, kwargs = calls[0]
    assert (bench, model, cases.name) == ("rule_extraction", "fake-model", "seed-policy")
    assert kwargs["dataset_version"] == "ru-policy-seed-v1.0"
    assert kwargs["fx_snapshot"] is cbr


def test_retry_failed_run_replaces_only_bad_case_and_keeps_attempt_history(monkeypatch, tmp_path):
    import docbench.run as R

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    good = {"case_id": "good", "ok": True, "finding_precision": 1.0, "cost_rub": 1.0,
            "latency_s": 0.1, "usage": {"served_model": "fake", "input_tokens": 1}}
    bad = {"case_id": "bad", "ok": False, "error": "HTTP 500", "cost_rub": None,
           "latency_s": None}
    original = {
        "benchmark": "conformance", "model": "fake", "cases_path": str(tmp_path / "cases"),
        "dataset_version": "test-v1", "fx_snapshot": None, "effort": "provider-default",
        "private": False, "artifacts": {"transcript": "transcript.json"}, "out_dir": str(run_dir),
        "started_at": "2026-08-18T00:00:00+00:00", "finished_at": "2026-08-18T00:00:01+00:00",
        "ts": "2026-08-18T00:00:01+00:00", "wall_time_s": 1.0, "n_cases": 2,
        "summary": R._aggregate([good, bad]), "cases": [good, bad],
    }
    (run_dir / "results.json").write_text(json.dumps(original), encoding="utf-8")
    (run_dir / "transcript.json").write_text(json.dumps({"cases": [
        {"case_id": "good", "attempts": [{"response_text": "old-good"}]},
        {"case_id": "bad", "attempts": [{"error": "HTTP 500"}]},
    ]}), encoding="utf-8")

    def fake_run(*args, **kwargs):
        assert kwargs["case_ids"] == {"bad"}
        out = kwargs["out_dir"]
        retried = {"case_id": "bad", "ok": True, "finding_precision": 1.0, "cost_rub": 2.0,
                   "latency_s": 0.2, "usage": {"served_model": "fake", "input_tokens": 2}}
        (out / "transcript.json").write_text(json.dumps({"cases": [
            {"case_id": "bad", "attempts": [{"response_text": "new-bad"}]},
        ]}), encoding="utf-8")
        return {"cases": [retried], "finished_at": "2026-08-18T00:00:03+00:00", "wall_time_s": 2.0,
                "cache_mode": "bypass",
                "summary": R._aggregate([retried])}

    monkeypatch.setattr(R, "run_benchmark", fake_run)
    merged = R.retry_failed_run(run_dir)
    assert merged["cases"][0] == good
    assert merged["summary"]["n_errors"] == 0
    assert merged["summary"]["total_cost_rub"] == 3.0
    assert merged["wall_time_s"] == 3.0
    assert merged["retry_history"][0]["case_ids"] == ["bad"]
    transcript = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))
    assert transcript["cases"][1]["attempts"][-1] == {"response_text": "new-bad", "retry": 1}


def test_explicit_safety_refusal_is_marked_without_changing_score_semantics():
    import docbench.run as R

    assert R._response_failure_kind("Я не могу обсуждать эту тему. Давайте поговорим о чём-нибудь ещё.") == "refusal"
    assert R._response_failure_kind("invalid response") is None
