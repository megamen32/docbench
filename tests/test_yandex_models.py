from docbench.config import resolve_model
import pytest


def test_yandex_models_use_configured_folder_id(monkeypatch):
    monkeypatch.setenv("DOCBENCH_YANDEX_API_KEY", "test-key")
    monkeypatch.setenv("DOCBENCH_YANDEX_FOLDER_ID", "folder-for-test")

    pro = resolve_model("yandexgpt-pro-5.1")
    alice = resolve_model("yandex-alice-ai-llm")

    assert pro.base_url == "https://ai.api.cloud.yandex.net/v1"
    assert pro.alias == "gpt://folder-for-test/yandexgpt-5.1"
    assert alice.alias == "gpt://folder-for-test/aliceai-llm"
    assert pro.price_currency == alice.price_currency == "USD"
    assert pro.price_in == pro.price_out == 6.557376
    assert alice.price_in == 4.09836
    assert alice.price_out == 9.836064


def test_yandex_model_requires_folder_id(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOCBENCH_YANDEX_API_KEY", "test-key")
    monkeypatch.delenv("DOCBENCH_YANDEX_FOLDER_ID", raising=False)

    with pytest.raises(RuntimeError, match="DOCBENCH_YANDEX_FOLDER_ID"):
        resolve_model("yandexgpt-pro-5.1")
