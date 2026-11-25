"""Tests for the Tahap 3 eval fix: grounding rescue + list handling.

The first full eval run scored 22/25: a single relevance threshold
refused two real questions whose top scores sat below it, and one
list question missed its expected source. These tests cover the
general mechanisms that fixed that, with synthetic data for the
decision rule and the real index for the pipeline behaviour.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import grounding  # noqa: E402
from ask import (  # noqa: E402
    assemble_list_results,
    assess_relevance,
    detect_list_intent,
)

INDEX_EXISTS = (ROOT / "output" / "index" / "index_info.json").exists()


def _chunk(text, doc_id="BUG-001", doc_type="bug_report", project="parabank"):
    return {
        "text": text,
        "metadata": {
            "doc_id": doc_id, "doc_type": doc_type, "project": project,
        },
    }


# ------------------------------------------------------- decision rule

_CORPUS = [
    _chunk("Order with quantity far above stock returns HTTP 500 error"),
    _chunk("Web login accepts an invalid password and opens the overview"),
    _chunk("Transfer larger than the balance is accepted by the form"),
]


def test_low_score_but_grounded_question_is_allowed():
    model = grounding.GroundingModel(_CORPUS)
    results = [{"score": 0.59, "chunk": _CORPUS[0]}]
    info = model.assess("What happens when quantity is far above stock?",
                        results)
    assert assess_relevance(results, info) is True


def test_low_score_ungrounded_question_is_refused():
    model = grounding.GroundingModel(_CORPUS)
    results = [{"score": 0.59, "chunk": _CORPUS[0]}]
    info = model.assess("What is the salary of the chief executive?",
                        results)
    assert info["weighted_union"] == 0.0
    assert assess_relevance(results, info) is False


def test_strong_score_needs_no_grounding():
    assert assess_relevance([{"score": 0.9, "chunk": _CORPUS[0]}], None) is True


def test_scattered_words_do_not_rescue_a_question():
    # "password" in one chunk and "database" in another must not add
    # up to a rescue: no single chunk covers the question.
    corpus = [
        _chunk("Login rejects an invalid password on the web form"),
        _chunk("The database stores one debit and one credit per transfer"),
    ]
    model = grounding.GroundingModel(corpus)
    results = [{"score": 0.59, "chunk": c} for c in corpus]
    info = model.assess("What is the production database password?",
                        results)
    assert assess_relevance(results, info) is False


# ------------------------------------------------------- list handling

def test_list_detection_english():
    is_list, types = detect_list_intent(
        "What bugs were found in the ParaBank demo application?"
    )
    assert is_list is True
    assert types == {"bug_report"}


def test_list_detection_indonesian():
    is_list, types = detect_list_intent(
        "Bug apa saja yang ditemukan di ParaBank?"
    )
    assert is_list is True
    assert types == {"bug_report"}


def test_single_record_question_is_not_a_list():
    is_list, _ = detect_list_intent(
        "Which bug was found in the ParaBank forgot password flow?"
    )
    assert is_list is False
    is_list, _ = detect_list_intent(
        "Which test case checks login with invalid credentials?"
    )
    assert is_list is False


def test_assemble_list_includes_enumerating_document():
    records = [
        {"score": 0.7, "chunk": _chunk("Bug ID: BUG-001 | Title: one", "BUG-001")},
        {"score": 0.6, "chunk": _chunk("Bug ID: BUG-002 | Title: two", "BUG-002")},
        {"score": 0.5, "chunk": _chunk("Bug ID: BUG-003 | Title: three", "BUG-003")},
    ]
    summary = {
        "score": 0.4,
        "chunk": _chunk(
            "Bugs I found: BUG-001, BUG-002 and BUG-003 are listed here.",
            "README-bugs", doc_type="document",
        ),
    }
    assembled = assemble_list_results(records + [summary], {"bug_report"})
    doc_ids = [r["chunk"]["metadata"]["doc_id"] for r in assembled]
    assert doc_ids[0] == "README-bugs"
    assert doc_ids[1:] == ["BUG-001", "BUG-002", "BUG-003"]


def test_assemble_list_without_enumeration_or_records():
    records = [
        {"score": 0.7, "chunk": _chunk("Bug ID: BUG-001 | Title: one", "BUG-001")},
    ]
    mention_one = {
        "score": 0.4,
        "chunk": _chunk("Only BUG-001 is mentioned here.", "README-x",
                        doc_type="document"),
    }
    assembled = assemble_list_results(records + [mention_one], {"bug_report"})
    assert [r["chunk"]["metadata"]["doc_id"] for r in assembled] == ["BUG-001"]
    assert assemble_list_results(records, {"test_case"}) is None


# --------------------------------------------------- pipeline (real)

@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_over_stock_question_is_rescued_by_grounding():
    from ask import ask_question

    out = ask_question(
        "What happens when a customer orders a quantity far above the "
        "available stock in Chaligula?",
        project="chaligula",
    )
    assert out["refused"] is False
    assert out["top_score"] < 0.65  # rescued, not passed on score
    assert any(
        s["doc_id"] == "BUG-001" and s["project"] == "chaligula"
        for s in out["sources"]
    )


@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_test_plan_risks_question_is_rescued_by_grounding():
    from ask import ask_question

    out = ask_question(
        "What risks are listed in the Chaligula test plan, for example "
        "about the free serverless tier?",
        project="chaligula",
    )
    assert out["refused"] is False
    assert any(
        s["doc_id"].startswith("test-plan-risks") for s in out["sources"]
    )


@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_list_question_returns_the_bugs_summary_source():
    from ask import ask_question

    out = ask_question(
        "What bugs were found in the ParaBank demo application while "
        "executing the tests?",
        project="parabank",
    )
    assert out["refused"] is False
    assert out["list_mode"] is True
    assert any(
        s["doc_id"].startswith("README-bugs-i-found")
        for s in out["sources"]
    )
    assert "BUG-001" in out["answer"] and "BUG-003" in out["answer"]
    assert out["citations_valid"] is True


@pytest.mark.skipif(not INDEX_EXISTS, reason="index not built yet")
def test_sms_otp_trap_is_still_refused():
    from ask import ask_question
    import llm

    out = ask_question(
        "Which bug was found in the ParaBank forgot password flow that "
        "sends an SMS OTP code?",
        project="parabank",
    )
    assert out["refused"] is True
    assert out["answer"] == llm.NOT_FOUND
    assert out["sources"] == []
