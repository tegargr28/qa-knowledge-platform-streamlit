"""Behaviour check for the Streamlit front end's ask path.

Runs all 25 golden questions through streamlit_core.answer_question()
— the exact function streamlit_app.py calls on every question — with
the app's default session settings (provider extractive, no key), and
scores them with the same rules as eval/run_eval.py:

- answerable: expected document among the returned sources, at least
  half of the expected keywords in the answer, citations valid, not
  refused.
- trap: passes only when the pipeline refuses (not-found answer, no
  sources).

The FastAPI pipeline scores 25/25 on this set (see
reports/eval_report.md). This check exists to prove the Streamlit
front end did not change that behaviour.

Usage:
    python eval/check_streamlit_pipeline.py [--report PATH]

Writes reports/streamlit_pipeline_check.md (or PATH) and exits 1 if
any question fails.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import llm  # noqa: E402
from retriever import Retriever  # noqa: E402
from streamlit_core import DEFAULT_SETTINGS, answer_question  # noqa: E402

QUESTIONS_FILE = ROOT / "eval" / "golden_questions.json"
REPORT_FILE = ROOT / "reports" / "streamlit_pipeline_check.md"


def source_matches(source, q):
    if source["project"] != q["project"]:
        return False
    if "expected_doc_id" in q:
        return source["doc_id"] == q["expected_doc_id"]
    return source["doc_id"].startswith(q["expected_doc_id_prefix"])


def expected_label(q):
    return q.get("expected_doc_id") or (q["expected_doc_id_prefix"] + "*")


def score_question(retriever, q):
    out = answer_question(
        q["question"], project=q["project"],
        settings=dict(DEFAULT_SETTINGS), retriever=retriever,
    )
    row = {
        "question": q["question"],
        "project": q["project"],
        "type": q["type"],
        "top_score": out.get("top_score"),
        "refused": bool(out.get("refused")),
    }
    if q["type"] == "trap":
        row["expected"] = "(refusal)"
        row["passed"] = (
            row["refused"] and out["answer"] == llm.NOT_FOUND
            and out["sources"] == []
        )
        row["detail"] = "refused" if row["passed"] else "NOT refused"
        return row
    row["expected"] = f"{q['project']}:{expected_label(q)}"
    row["source_hit"] = any(source_matches(s, q) for s in out["sources"])
    answer_lower = out["answer"].lower()
    hits = [kw for kw in q["expected_keywords"] if kw.lower() in answer_lower]
    row["keyword_hits"] = f"{len(hits)}/{len(q['expected_keywords'])}"
    row["keywords_ok"] = len(hits) * 2 >= len(q["expected_keywords"])
    row["citations_valid"] = bool(out["citations_valid"])
    row["passed"] = (
        row["source_hit"] and row["keywords_ok"] and row["citations_valid"]
        and not row["refused"]
    )
    reasons = []
    if row["refused"]:
        reasons.append("refused by threshold")
    if not row["source_hit"]:
        reasons.append("expected source not in returned sources")
    if not row["keywords_ok"]:
        reasons.append(f"keywords only {row['keyword_hits']}")
    if not row["citations_valid"]:
        reasons.append("citations invalid")
    row["detail"] = "ok" if row["passed"] else "; ".join(reasons)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=str(REPORT_FILE))
    args = parser.parse_args()

    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    retriever = Retriever()
    rows = [score_question(retriever, q) for q in questions]

    passed = sum(r["passed"] for r in rows)
    total = len(rows)
    ans = [r for r in rows if r["type"] == "answerable"]
    traps = [r for r in rows if r["type"] == "trap"]

    lines = [
        "# Streamlit pipeline check",
        "",
        "All golden questions run through streamlit_core.answer_question() "
        "(the function streamlit_app.py calls), with the app's default "
        "session settings (extractive, no key). Scoring rules are the "
        "same as eval/run_eval.py.",
        "",
        f"Score: {passed}/{total}",
        f"Answerable passed: {sum(r['passed'] for r in ans)}/{len(ans)}. "
        f"Traps refused: {sum(r['passed'] for r in traps)}/{len(traps)}.",
        "",
        "| # | Type | Question | Expected | Top score | Result | Detail |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        q_short = r["question"][:80].replace("|", "/")
        lines.append(
            f"| {i} | {r['type']} | {q_short} | {r['expected']} | "
            f"{r['top_score']} | {'PASS' if r['passed'] else 'FAIL'} | "
            f"{r['detail']} |"
        )
    report = "\n".join(lines) + "\n"
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
