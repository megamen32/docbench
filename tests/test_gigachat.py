from types import SimpleNamespace

from docbench.models.gigachat import GigaChatRunner
from docbench.config import resolve_model


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_gigachat_mints_and_reuses_access_token(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return _Response(200, {"access_token": "ephemeral-token", "expires_at": 4_102_444_800})

    monkeypatch.setattr("docbench.models.gigachat.requests.post", post)
    spec = SimpleNamespace(
        ca_bundle=None,
        oauth_url="https://oauth.example/api/v2/oauth",
        oauth_scope="GIGACHAT_API_PERS",
        ca_bundle_env="DOCBENCH_GIGACHAT_CA_BUNDLE",
    )
    runner = object.__new__(GigaChatRunner)
    runner.spec = spec
    runner.model_key = "gigachat-3-ultra"
    runner._api_key = "authorization-key"
    runner.timeout = 3
    runner._verify = True
    runner._access_token = None
    runner._access_token_expires_at = 0

    first = runner._request_headers()
    second = runner._request_headers()

    assert first["Authorization"] == "Bearer ephemeral-token"
    assert second["Authorization"] == "Bearer ephemeral-token"
    assert len(calls) == 1
    assert calls[0][1]["data"] == {"scope": "GIGACHAT_API_PERS"}
    assert calls[0][1]["headers"]["Authorization"] == "Basic authorization-key"


def test_gigachat_model_catalog_uses_oauth(monkeypatch):
    monkeypatch.setenv("SBER", "test-authorization-key")
    model = resolve_model("gigachat-3-ultra")

    assert model.alias == "GigaChat-3-Ultra"
    assert model.auth_method == "gigachat_oauth"
    assert model.oauth_scope == "GIGACHAT_API_PERS"
