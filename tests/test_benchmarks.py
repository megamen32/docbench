"""Offline end-to-end: canned oracle-perfect reply flows through parse+score
and through the full run orchestrator via a pre-seeded response cache."""
import json
from pathlib import Path

from docbench.benchmarks.base import load_case
from docbench.benchmarks.conformance import ConformanceBenchmark
from docbench.benchmarks.rule_extraction import RuleExtractionBenchmark
from docbench.benchmarks.base import load_ruleset
from docbench.oracle import flatten_case, gold_for

REPO = Path(__file__).resolve().parent.parent


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
    cache.mkdir(parents=True, exist_ok=True)
    msgs = bench.messages(valid_case, gold)
    comp = R.OpenAICompatRunner.complete(runner, msgs) if False else None
    # seed the cache the way the runner itself would
    key = runner._cache_key(msgs, 0.0, 8192)
    runner._cache_put(key, type("C", (), {"text": reply, "usage": {"prompt_tokens": 10, "completion_tokens": 10},
                                          "latency_s": 0.1, "cost_usd": 0.0,
                                          "cost_is_estimate": True, "model": "fake",
                                          "cache_hit": False})())

    # point the orchestrator at our runner factory state
    monkeypatch.setattr(R, "CACHE_DIR", cache)
    monkeypatch.setattr(R, "resolve_model", lambda k, allow_missing_key=False: spec)
    monkeypatch.setattr(R, "OpenAICompatRunner", lambda s, cache_dir=None, offline=False:
                        runner)

    case_file = tmp_path / "c.yaml"
    import yaml
    case_file.write_text(yaml.safe_dump(valid_case.model_dump(exclude_none=True),
                                        allow_unicode=True, sort_keys=False), encoding="utf-8")
    res = R.run_benchmark("conformance", "fake", case_file,
                          ruleset_dir=REPO / "rulesets", out_dir=tmp_path / "out")
    assert res["summary"]["case_pass_rate"] == 1.0
    assert res["summary"]["finding_f1"] == 1.0
    transcript = json.loads((tmp_path / "out" / "transcript.json").read_text(encoding="utf-8"))
    assert res["artifacts"]["transcript"] == "transcript.json"
    assert transcript["cases"][0]["attempts"][0]["response_text"] == reply
