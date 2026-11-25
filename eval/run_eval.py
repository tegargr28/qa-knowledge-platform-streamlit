"""Full answer evaluation for the QA Knowledge Platform (Tahap 3).

Runs all 25 golden questions in eval/golden_questions.json through the
FULL ask pipeline (retriever + extractive provider + citation
validator), using the same ask_question() code path as POST /ask. The
provider is forced to extractive so the run needs no API key and is
repeatable.

Scoring:
- answerable questions pass when the expected document is among the
  returned sources, at least half of the expected keywords appear in
  the answer, and the citations are valid.
- trap questions pass only when the system refuses: the not-found
  answer, no sources, triggered by the refusal rule in ask.py (score
  threshold combined with the grounding check in grounding.py).

The gate is 80%: below it the script prints GATE: FAIL and exits 1.

Usage:
    python eval/run_eval.py [--report PATH]

Writes reports/eval_report.md (or PATH) with the per-question table
and the threshold calibration numbers.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import llm  # noqa: E402
from ask import (  # noqa: E402
    GROUNDING_BEST_MIN,
    GROUNDING_UNION_MIN,
    RELEVANCE_THRESHOLD,
    ask_question,
)
from retriever import Retriever  # noqa: E402

QUESTIONS_FILE = ROOT / "eval" / "golden_questions.json"
REPORT_FILE = ROOT / "reports" / "eval_report.md"
GATE = 0.80


def source_matches(source, q):
    if source["project"] != q["project"]:
        return False
    if "expected_doc_id" in q:
        return source["doc_id"] == q["expected_doc_id"]
    return source["doc_id"].startswith(q["expected_doc_id_prefix"])


def expected_label(q):
    return q.get("expected_doc_id") or (q["expected_doc_id_prefix"] + "*")


def score_question(retriever, q):
    out = ask_question(
        q["question"], project=q["project"], retriever=retriever,
        llm_overrides={"provider": "extractive"},
    )
    grounding_info = out.get("grounding") or {}
    row = {
        "question": q["question"],
        "project": q["project"],
        "type": q["type"],
        "top_score": out.get("top_score"),
        "refused": bool(out.get("refused")),
        "answer": out["answer"],
        "grounding_union": grounding_info.get("weighted_union"),
        "grounding_best": grounding_info.get("weighted_best"),
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
    score = passed / total
    gate_pass = score >= GATE
    ans = [r for r in rows if r["type"] == "answerable"]
    traps = [r for r in rows if r["type"] == "trap"]
    ans_top = [r["top_score"] for r in ans if r["top_score"] is not None]
    trap_top = [r["top_score"] for r in traps if r["top_score"] is not None]
    low_ans = [
        r for r in ans
        if r["top_score"] is not None and r["top_score"] < RELEVANCE_THRESHOLD
    ]

    lines = [
        "# Full answer evaluation report (Tahap 3)",
        "",
        f"Pipeline: retriever + extractive provider + citation validator, "
        f"the same ask_question() path as POST /ask. Questions: {total} "
        f"({len(ans)} answerable, {len(traps)} traps) from "
        "eval/golden_questions.json.",
        "",
        f"Score: {passed}/{total} ({score:.0%})",
        f"GATE (80%): {'PASS' if gate_pass else 'FAIL'}",
        f"Answerable passed: {sum(r['passed'] for r in ans)}/{len(ans)}. "
        f"Traps refused: {sum(r['passed'] for r in traps)}/{len(traps)}.",
        "",
        "## Refusal rule: score threshold plus grounding check",
        "",
        f"A question is refused before any provider is called when its "
        f"top retrieved chunk scores below {RELEVANCE_THRESHOLD} AND its "
        "distinctive words are not demonstrably present in the retrieved "
        "text (the grounding check in src/grounding.py, rarity-weighted "
        "term coverage over the top 3 chunks). Below the score threshold "
        f"an answer is still allowed when weighted union coverage is at "
        f"least {GROUNDING_UNION_MIN} and the best single chunk covers "
        f"at least {GROUNDING_BEST_MIN}.",
        "",
        f"Top scores of the {len(ans)} answerable questions: "
        f"min {min(ans_top):.3f}, max {max(ans_top):.3f}.",
        f"Top scores of the {len(traps)} trap questions: "
        f"min {min(trap_top):.3f}, max {max(trap_top):.3f}.",
        "The score ranges overlap, which is why the score alone is not "
        "the whole rule.",
        "",
        "Measured grounding (weighted union / weighted best chunk):",
    ]
    for r in low_ans:
        lines.append(
            f"- Answerable below the score threshold: \"{r['question'][:70]}\" "
            f"score {r['top_score']}, grounding "
            f"{r['grounding_union']} / {r['grounding_best']}."
        )
    for r in traps:
        lines.append(
            f"- Trap: \"{r['question'][:70]}\" score {r['top_score']}, "
            f"grounding {r['grounding_union']} / {r['grounding_best']}."
        )
    lines += [
        "",
        "## Fix history",
        "",
        "First full run (score threshold only): 22/25 (88%), GATE PASS, "
        "traps refused 5/5, but two real questions were refused by the "
        "threshold and one list question missed its expected source. "
        "Fix applied: the grounding rescue above, plus general list "
        "handling (wider search, records of the asked type, and the "
        "project document chunk that enumerates those same records "
        "included as a source; list answers enumerate the records). "
        f"This run: {passed}/{total} ({score:.0%}).",
        "",
        "## Per-question results",
        "",
        "| # | Type | Question | Expected | Top score | Grounding | Result | Detail |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        q_short = r["question"][:80].replace("|", "/")
        lines.append(
            f"| {i} | {r['type']} | {q_short} | {r['expected']} | "
            f"{r['top_score']} | "
            f"{r['grounding_union']} / {r['grounding_best']} | "
            f"{'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |"
        )
    report = "\n".join(lines) + "\n"
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"GATE: {'PASS' if gate_pass else 'FAIL'} ({passed}/{total})")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
