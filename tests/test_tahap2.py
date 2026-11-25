import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import llm  # noqa: E402
import validator  # noqa: E402

CHUNKS = [
    {
        "id": "chaligula:test-cases.xlsx:bug-reports:BUG-001:5",
        "text": "Bug ID: BUG-001 | Title / Summary: Order above stock returns HTTP 500",
        "metadata": {
            "project": "chaligula", "doc_id": "BUG-001",
            "sheet": "Bug Reports", "doc_type": "bug_report",
        },
    },
    {
        "id": "parabank:test-cases.xlsx:bug-reports:BUG-001:5",
        "text": "Bug ID: BUG-001 | Title / Summary: Web login accepts an invalid password",
        "metadata": {
            "project": "parabank", "doc_id": "BUG-001",
            "sheet": "Bug Reports", "doc_type": "bug_report",
        },
    },
]


# ------------------------------------------------------------- validator

def test_validator_accepts_real_citation():
    answer = "Ordering far above stock returns HTTP 500 [chaligula:BUG-001]."
    result = validator.validate_citations(answer, CHUNKS)
    assert result["valid"] is True
    assert result["invalid"] == []


def test_validator_rejects_fabricated_citation():
    answer = "This is documented in [parabank:BUG-999] and [chaligula:BUG-001]."
    result = validator.validate_citations(answer, CHUNKS)
    assert result["valid"] is False
    assert result["invalid"] == ["parabank:BUG-999"]


def test_validator_rejects_answer_without_citations():
    result = validator.validate_citations("No sources named here.", CHUNKS)
    assert result["valid"] is False


def test_validator_project_matters_for_duplicate_doc_ids():
    # Both projects have a BUG-001. Citing the wrong project must fail
    # when only the other project's chunk was retrieved.
    result = validator.validate_citations(
        "See [chaligula:BUG-001].", [CHUNKS[1]]
    )
    assert result["valid"] is False


# ------------------------------------------------- openai-compatible BYOK

def test_openai_compatible_request_payload(monkeypatch):
    captured = {}

    def fake_post(url, payload, headers=None):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return {"choices": [{"message": {"content": "Answer [chaligula:BUG-001]"}}]}

    monkeypatch.setattr(llm, "_post_json", fake_post)
    result = llm.answer(
        "What happens when ordering above stock?",
        CHUNKS,
        overrides={
            "provider": "openai-compatible",
            "api_key": "test-key-not-real",
            "model": "my-chosen-model",
            "base_url": "https://example.invalid/v1",
        },
    )
    assert captured["url"] == "https://example.invalid/v1/chat/completions"
    assert captured["payload"]["model"] == "my-chosen-model"
    assert captured["headers"]["Authorization"] == "Bearer test-key-not-real"
    assert result["provider"] == "openai-compatible"
    assert result["fell_back"] is False


def test_no_key_falls_back_to_extractive():
    result = llm.answer(
        "What happens when ordering above stock?",
        CHUNKS,
        overrides={"provider": "openai-compatible", "api_key": "", "model": "x"},
    )
    assert result["provider"] == "extractive"
    assert result["fell_back"] is True
    assert "chaligula:BUG-001" in result["answer"]


# ------------------------------------------------------- settings masking

def test_settings_never_expose_key(tmp_path, monkeypatch):
    settings_file = tmp_path / "llm_settings.json"
    monkeypatch.setattr(llm, "SETTINGS_FILE", settings_file)
    public = llm.save_settings(
        {
            "provider": "openai-compatible",
            "api_key": "super-secret-test-value",
            "model": "my-chosen-model",
            "base_url": "https://example.invalid/v1",
        }
    )
    assert public["key_set"] is True
    assert "super-secret-test-value" not in str(public)

    import app as app_module

    get_result = app_module.get_llm_settings()
    assert get_result["key_set"] is True
    assert "super-secret-test-value" not in str(get_result)


# --------------------------------------------------------- retriever smoke

def test_retriever_overstock_question_finds_chaligula_bug():
    index = ROOT / "output" / "index" / "index_info.json"
    if not index.exists():
        pytest.skip("index not built yet")
    from retriever import Retriever

    retriever = Retriever()
    results = retriever.search(
        "What happens when a customer orders a quantity far above the "
        "available stock?",
        k=5, project="chaligula",
    )
    found = [
        r["chunk"]["metadata"]["doc_id"] for r in results
    ]
    assert "BUG-001" in found
