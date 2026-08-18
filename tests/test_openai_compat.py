from types import SimpleNamespace

from docbench.models.openai_compat import OpenAICompatRunner
from docbench.config import resolve_model


class _Response:
    status_code = 200

    def json(self):
        return {
            "model": "served-test",
            "choices": [{"message": {"content": "<think>private chain</think>\nFINAL"}}],
            "usage": {},
        }


def test_runner_does_not_persist_closed_think_block(monkeypatch):
    spec = SimpleNamespace(
        key="test", alias="test", base_url="https://example.invalid/v1", api_key="test",
        price_currency="USD", price_in=None, price_out=None,
        price_cache_read=None, price_cache_write=None,
    )
    monkeypatch.setattr("docbench.models.openai_compat.requests.post", lambda *a, **kw: _Response())

    completion = OpenAICompatRunner(spec, max_retries=1).complete(
        [{"role": "user", "content": "test"}], max_tokens=8
    )

    assert completion.text == "FINAL"


def test_omniroute_defaults_to_explicit_thinking_disable(monkeypatch):
    monkeypatch.setenv("DOCBENCH_OMNIROUTE_API_KEY", "test-key")

    model = resolve_model("omniroute-routerai-gpt-5.4-mini")

    assert model.effort_default == "no_thinking"
    assert model.effort_extra(None) == {"thinking": False}
