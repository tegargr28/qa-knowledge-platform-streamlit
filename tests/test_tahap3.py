import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import llm  # noqa: E402
from ask import RELEVANCE_THRESHOLD, passes_relevance  # noqa: E402

INDEX_EXISTS = (ROOT / "output" / "index" / "index_info.json").exists()


# ------------------------------------------------------- threshold logic

def test_threshold_accepts_strong_top_result():
    assert passes_relevance([{"score": RELEVANCE_THRESHOLD + 0.1}]) is True


def test_threshold_rejects_weak_top_result():
    assert passes_relevance([{"score": RELEVANCE_THRESHOLD - 0.1}]) is False


def test_threshold_rejects_empty_results():
    assert passes_relevance([]) is False


def test_threshold_boundary_is_inclusive():
    assert passes_relevance([{"score": 0.5}], threshold=0.5) is True
    assert passes_relevance([{"score": 0.49}], threshold=0.5) is False


# --------------------------------------------------- trap refusal (real)

@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_trap_question_is_refused_by_the_pipeline():
    from ask import ask_question

    out = ask_question("Who is the CEO of ParaBank?", project="parabank")
    assert out["refused"] is True
    assert out["answer"] == llm.NOT_FOUND
    assert out["sources"] == []
    assert out["citations_valid"] is True


@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_real_question_is_not_refused():
    from ask import ask_question

    out = ask_question(
        "What bug was found when logging in to the ParaBank web "
        "application with an invalid password?",
        project="parabank",
    )
    assert out["refused"] is False
    assert out["sources"]
    assert out["citations_valid"] is True


# ------------------------------------------------------------ chat page

def test_chat_page_is_served():
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("FastAPI TestClient (httpx) not available")
    import app as app_module

    client = TestClient(app_module.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "QA Knowledge Platform" in resp.text
    assert 'id="question"' in resp.text
    assert 'id="settings"' in resp.text
    # The settings panel must not contain any prefilled API key field.
    assert 'id="api_key"' in resp.text
    assert 'value="sk-' not in resp.text
