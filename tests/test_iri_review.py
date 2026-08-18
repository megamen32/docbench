import json
import subprocess
from pathlib import Path

import yaml

from docbench.benchmarks.base import load_case
from docbench.benchmarks.iri_review import IriReviewBenchmark
from docbench.run import _write_transcript


def _fixture(tmp_path: Path):
    packet = tmp_path / "packet.md"
    packet.write_text("# Обезличенный пакет\n\nКоманда проекта\n", encoding="utf-8")
    case_path = tmp_path / "case.yaml"
    case_path.write_text(yaml.safe_dump({
        "id": "iri-test",
        "benchmark": "iri_review",
        "documents": {"packet": {"kind": "packet", "text_file": "packet.md"}},
    }, allow_unicode=True), encoding="utf-8")
    gold_path = tmp_path / "gold.yaml"
    gold_path.write_text(yaml.safe_dump({
        "case_id": "iri-test",
        "findings": [{
            "id": "IRI-001",
            "field": "Команда проекта",
            "match_groups": [["квалификац"], ["менее одного года"]],
        }],
    }, allow_unicode=True), encoding="utf-8")
    return case_path, gold_path


def test_iri_case_loads_external_text_and_scores_gold(tmp_path):
    case_path, gold_path = _fixture(tmp_path)
    case = load_case(case_path)
    assert case.documents["packet"].text == "# Обезличенный пакет\n\nКоманда проекта\n"

    bench = IriReviewBenchmark(gold_path)
    reply = json.dumps({"findings": [{
        "field": "Команда проекта",
        "canonical": "Необходимо доработать поле «Команда проекта». Квалификация менее одного года.",
        "requirement": "не менее одного года",
        "evidence": "packet.md",
        "fix": "загрузить подтверждение",
    }]}, ensure_ascii=False)
    pred, err = bench.parse(reply, case)
    assert err is None
    scores = bench.score(pred, bench.gold_for(case), case)
    assert scores["ok"] is True
    assert scores["gold_points"] == 1


def test_iri_parser_rejects_free_text_and_noncanonical_finding(tmp_path):
    case_path, gold_path = _fixture(tmp_path)
    case = load_case(case_path)
    bench = IriReviewBenchmark(gold_path)
    pred, err = bench.parse("intro\n" + json.dumps({"findings": []}), case)
    assert pred is not None and err is None  # extractor tolerates a reasoning wrapper

    bad, warning = bench.parse(json.dumps({"findings": [{"field": "x"}]}), case)
    assert bad["findings"] == []
    assert warning == "1 malformed findings dropped"


def test_private_transcript_is_written_only_as_gitcrypt_ciphertext(tmp_path, monkeypatch):
    def fake_clean(*args, **kwargs):
        assert args[0] == ["git-crypt", "clean"]
        assert kwargs["input"]
        return subprocess.CompletedProcess(args[0], 0, b"\x00GITCRYPT\x00cipher", b"")

    monkeypatch.setattr("docbench.run.subprocess.run", fake_clean)
    path = _write_transcript(tmp_path, {"cases": [{"messages": [{"content": "secret"}]}]}, private=True)

    assert path.name == "transcript.json.gitcrypt"
    assert path.read_bytes() == b"\x00GITCRYPT\x00cipher"
    assert not (tmp_path / "transcript.json").exists()
