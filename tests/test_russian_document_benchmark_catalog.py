from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO / "datasets" / "russian_document_benchmark_catalog.yaml"
MARKDOWN_PATH = REPO / "RUSSIAN_DOCUMENT_BENCHMARK_CATALOG.md"


def _catalog():
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


def test_russian_catalog_has_accepted_primary_document_track():
    data = _catalog()

    assert data["schema_version"] == 2
    assert data["status"] == "accepted"
    assert data["primary_language"] == "ru"
    assert data["fixture_admission"]["require_verified_usage_rights"] is True

    primary = data["primary_document_tasks"]
    assert len(primary) == 6
    assert {task["catalog_label"] for task in primary} == {
        "LabTabVQA",
        "ruMathVQA",
        "ruNaturalScienceVQA",
        "ruTiE-Image",
        "SchoolScienceVQA",
        "UniScienceVQA",
    }
    assert all(task["language"] == "ru" for task in primary)
    assert all("document_page_image" in task["input"] for task in primary)
    assert all("evidence_grounding" in task["metrics"] for task in primary)


def test_russian_catalog_retains_all_supporting_tracks_without_urls():
    data = _catalog()
    assert len(data["auxiliary_visual_tasks"]) == 5
    assert len(data["domain_knowledge_tasks"]) == 3
    assert len(data["supplemental_reasoning_tasks"]) == 4

    text = MARKDOWN_PATH.read_text(encoding="utf-8")
    assert "http://" not in text
    assert "https://" not in text
    assert "Это постоянная спецификация покрытия русского бенчмарка." in text

    labels = [
        task["catalog_label"]
        for track in (
            "primary_document_tasks",
            "auxiliary_visual_tasks",
            "domain_knowledge_tasks",
            "supplemental_reasoning_tasks",
        )
        for task in data[track]
    ]
    assert all(label in text for label in labels)
