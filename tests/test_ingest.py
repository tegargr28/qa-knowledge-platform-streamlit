import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import ingest  # noqa: E402


def load_chunks():
    path = ROOT / "output" / "chunks.jsonl"
    assert path.exists(), "run src/ingest.py first"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_empty_rows_are_skipped():
    chunks = load_chunks()
    # No chunk may be built only from empty fields.
    assert all(c["text"].strip() for c in chunks)
    # The report counts skipped empty rows; the templates carry many of them.
    report = (ROOT / "reports" / "ingest_report.md").read_text(encoding="utf-8")
    assert "Empty rows skipped:" in report
    skipped = int(report.split("Empty rows skipped:")[1].splitlines()[0].strip())
    assert skipped > 0


def test_known_bug_chunks_exist_with_correct_doc_id():
    chunks = load_chunks()
    parabank_bug = [
        c for c in chunks
        if c["metadata"]["project"] == "parabank"
        and c["metadata"]["doc_type"] == "bug_report"
        and c["metadata"]["doc_id"] == "BUG-001"
    ]
    assert parabank_bug, "ParaBank BUG-001 chunk missing"
    assert "invalid password" in parabank_bug[0]["text"]

    chaligula_bug = [
        c for c in chunks
        if c["metadata"]["project"] == "chaligula"
        and c["metadata"]["doc_type"] == "bug_report"
        and c["metadata"]["doc_id"] == "BUG-001"
    ]
    assert chaligula_bug, "Chaligula BUG-001 chunk missing"
    assert "500" in chaligula_bug[0]["text"]


def test_ingest_is_deterministic(tmp_path, monkeypatch):
    first = (ROOT / "output" / "chunks.jsonl").read_bytes()
    ingest.main()
    second = (ROOT / "output" / "chunks.jsonl").read_bytes()
    assert first == second
