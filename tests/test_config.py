from docbench.config import resolve_model


def test_yandex_legacy_env_names_are_supported(monkeypatch):
    monkeypatch.setenv("YANDEX", "test-key")
    monkeypatch.setenv("YANDEX_FOLDER", "test-folder")
    monkeypatch.delenv("DOCBENCH_YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("DOCBENCH_YANDEX_FOLDER_ID", raising=False)

    model = resolve_model("yandexgpt-pro-5.1")

    assert model.api_key == "test-key"
    assert model.alias == "gpt://test-folder/yandexgpt-5.1"
