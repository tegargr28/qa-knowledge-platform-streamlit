"""Retrieval evaluation for the QA Knowledge Platform (Tahap 2).

Runs the fixed questions in eval/retrieval_questions.json against the
retriever only (no LLM involved) and reports Hit@1 and Hit@5: did the
expected document appear as the first result, or anywhere in the top 5?

A question counts as a hit when a returned chunk matches both the
expected project and the expected document ID (or ID prefix).

Usage:
    python eval/run_retrieval_eval.py [--hybrid | --no-hybrid]

Writes reports/retrieval_eval.md for the mode that was run last, and
prints both the per-question table and the totals.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from retriever import Retriever  # noqa: E402

QUESTIONS_FILE = ROOT / "eval" / "retrieval_questions.json"
REPORT_FILE = ROOT / "reports" / "retrieval_eval.md"


def matches(chunk, expected):
    meta = chunk["metadata"]
    if meta["project"] != expected["expected_project"]:
        return False
    if "expected_doc_id" in expected:
        return meta["doc_id"] == expected["expected_doc_id"]
    return meta["doc_id"].startswith(expected["expected_doc_id_prefix"])


def expected_label(expected):
    return expected.get("expected_doc_id") or (
        expected["expected_doc_id_prefix"] + "*"
    )


def run(retriever, questions, hybrid):
    rows = []
    for q in questions:
        results = retriever.search(
            q["question"], k=5, project=q["expected_project"], hybrid=hybrid
        )
        hit_positions = [
            i + 1 for i, r in enumerate(results) if matches(r["chunk"], q)
        ]
        rows.append(
            {
                "question": q["question"],
                "expected": f"{q['expected_project']}:{expected_label(q)}",
                "top1": (
                    f"{results[0]['chunk']['metadata']['project']}:"
                    f"{results[0]['chunk']['metadata']['doc_id']}"
                    if results else "(none)"
                ),
                "hit_at_1": bool(hit_positions and hit_positions[0] == 1),
                "hit_at_5": bool(hit_positions),
                "position": hit_positions[0] if hit_positions else None,
            }
        )
    return rows


def summarise(rows):
    n = len(rows)
    return {
        "n": n,
        "hit_at_1": sum(r["hit_at_1"] for r in rows),
        "hit_at_5": sum(r["hit_at_5"] for r in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--hybrid", dest="hybrid", action="store_true", default=True)
    group.add_argument("--no-hybrid", dest="hybrid", action="store_false")
    parser.add_argument("--report", default=str(REPORT_FILE))
    args = parser.parse_args()

    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    retriever = Retriever()
    rows = run(retriever, questions, hybrid=args.hybrid)
    totals = summarise(rows)
    mode = "hybrid (vector + keyword bonus)" if args.hybrid else "pure vector"

    lines = [
        "# Retrieval evaluation report",
        "",
        f"Embedding provider: {retriever.info['provider']} "
        f"({retriever.info['model']}), {retriever.info['chunk_count']} chunks indexed.",
        f"Scoring mode: {mode}. Questions: {totals['n']} (fixed set in "
        "eval/retrieval_questions.json, run against the retriever only).",
        "",
        f"Hit@1: {totals['hit_at_1']}/{totals['n']} "
        f"({totals['hit_at_1'] / totals['n']:.0%})",
        f"Hit@5: {totals['hit_at_5']}/{totals['n']} "
        f"({totals['hit_at_5'] / totals['n']:.0%})",
        "",
        "| # | Question | Expected | Top 1 returned | Hit@1 | Hit@5 |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['question']} | {r['expected']} | {r['top1']} | "
            f"{'yes' if r['hit_at_1'] else 'no'} | "
            f"{'yes' if r['hit_at_5'] else 'no'} |"
        )
    report = "\n".join(lines) + "\n"
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    return totals


if __name__ == "__main__":
    main()
