from types import SimpleNamespace

from docbench.models.openai_compat import OpenAICompatRunner
from docbench.models.usage import normalize_usage
from docbench.run import render_markdown_report
import docbench.run as R


def test_normalize_openai_cached_tokens_without_double_counting():
    usage = normalize_usage({
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "total_tokens": 110,
        "prompt_tokens_details": {"cached_tokens": 40},
        "completion_tokens_details": {"reasoning_tokens": 3},
    })
    assert usage["input_tokens"] == 100
    assert usage["uncached_input_tokens"] == 60
    assert usage["cache_read_input_tokens"] == 40
    assert usage["total_tokens"] == 110
    assert usage["reasoning_tokens"] == 3


def test_normalize_additive_cache_usage():
    usage = normalize_usage({
        "input_tokens": 60,
        "cache_read_input_tokens": 40,
        "output_tokens": 10,
    })
    assert usage["input_tokens"] == 100
    assert usage["uncached_input_tokens"] == 60
    assert usage["total_tokens"] == 110


def test_cost_charges_cached_input_once():
    runner = object.__new__(OpenAICompatRunner)
    runner.spec = SimpleNamespace(
        price_in=2.0, price_out=4.0,
        price_cache_read=None, price_cache_write=None,
    )
    cost = runner._cost({
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "prompt_tokens_details": {"cached_tokens": 40},
    })
    assert cost == 0.00024


def test_markdown_separates_reasoning_and_token_counts():
    report = render_markdown_report([{
        "model": "luna",
        "benchmark": "conformance",
        "reasoning": True,
        "reasoning_note": "matters",
        "summary": {"tokens": {
            "input_tokens": 100, "output_tokens": 20, "total_tokens": 120,
            "cache_read_input_tokens": 40, "cache_write_input_tokens": 0,
            "reasoning_tokens": 8,
        }, "total_cost_rub": 0.12},
        "cases": [],
    }])
    assert "- reason=matters" in report
    assert "| input | output | total | cache read | cache write | reasoning | cost RUB |" in report
    assert "| 100 | 20 | 120 | 40 | 0 | 8 | 0.12 |" in report


def test_fetch_cbr_usd_rub_parses_official_daily_xml(monkeypatch):
    xml = b'''<?xml version="1.0" encoding="windows-1251"?>
    <ValCurs Date="18.08.2026" name="Foreign Currency Market">
      <Valute ID="R01235"><CharCode>USD</CharCode><Nominal>1</Nominal><Value>81,2500</Value></Valute>
    </ValCurs>'''

    class Response:
        def read(self):
            return xml

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(R, "urlopen", lambda *args, **kwargs: Response())
    snapshot = R.fetch_cbr_usd_rub()
    assert snapshot == {
        "usd_rub": 81.25,
        "date": "2026-08-18",
        "source": "CBR",
        "source_url": R.CBR_DAILY_URL,
    }
