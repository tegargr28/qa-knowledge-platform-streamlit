"""Retriever for the QA Knowledge Platform (Tahap 2).

Loads the local index built by embed_index.py and answers: given a
question, which chunks are most relevant?

Two rules from the enterprise design in docs/DESIGN.md are already in
place here, even in personal mode:

- The project filter and the permission filter (allowed_projects) are
  applied to the candidate set BEFORE any result is returned, never as
  an afterthought on the top results. In personal mode allowed_projects
  is simply every project, because Tegar is the only member and holds
  every role.
- Nothing outside this module knows how the index is stored, so
  pgvector or Qdrant can replace the .npy files later.

Scoring: cosine similarity on the normalised vectors. An optional
hybrid mode adds a small keyword overlap bonus and a small penalty for
"other" chunks (the workbook Test Summary rows), which otherwise crowd
the top results with aggregate numbers instead of the actual bug or
test case a question asks about. Hybrid is on by default; the retrieval
evaluation in eval/ reports both modes.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import embeddings

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "output" / "index"

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "a", "an", "what", "is", "are", "does", "do", "did", "in",
    "on", "of", "for", "to", "with", "when", "which", "bug", "test",
    "case", "about", "that", "this", "it", "if", "or", "and",
}


def _keywords(text):
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


class Retriever:
    def __init__(self, index_dir=INDEX_DIR):
        index_dir = Path(index_dir)
        self.vectors = np.load(index_dir / "vectors.npy")
        self.chunks = json.loads(
            (index_dir / "chunks_meta.json").read_text(encoding="utf-8")
        )
        self.info = json.loads(
            (index_dir / "index_info.json").read_text(encoding="utf-8")
        )
        if self.info["provider"] == "tfidf":
            state = json.loads(
                (index_dir / "tfidf_state.json").read_text(encoding="utf-8")
            )
            self.provider = embeddings.TFIDFProvider.from_state(state)
        else:
            self.provider = embeddings.SentenceTransformerProvider(
                self.info["model"]
            )

    def search(self, question, k=5, project="all", allowed_projects=None,
               hybrid=True):
        """Return top-k chunks: [{chunk, score, vector_score}].

        project: "all", "parabank" or "chaligula".
        allowed_projects: permission filter. None means every project is
        allowed (personal mode). Applied before ranking.
        """
        query_vec = self.provider.embed_query(question)
        scores = self.vectors @ query_vec

        candidates = []
        for i, chunk in enumerate(self.chunks):
            meta = chunk["metadata"]
            if project not in (None, "all") and meta["project"] != project:
                continue
            if allowed_projects is not None and meta["project"] not in allowed_projects:
                continue
            candidates.append(i)

        question_kw = _keywords(question)
        raw_tokens = set(_TOKEN_RE.findall(question.lower()))
        results = []
        for i in candidates:
            chunk = self.chunks[i]
            vector_score = float(scores[i])
            final = vector_score
            if hybrid:
                text_kw = _keywords(chunk["text"])
                overlap = (
                    len(question_kw & text_kw) / len(question_kw)
                    if question_kw else 0.0
                )
                final += 0.15 * overlap
                # Exact document ID mentioned in the question is a
                # very strong signal.
                doc_id = chunk["metadata"].get("doc_id", "")
                if doc_id and doc_id.lower() in question.lower():
                    final += 0.30
                doc_type = chunk["metadata"].get("doc_type")
                if doc_type == "other":
                    final -= 0.05
                # Intent bonus: a question that asks about a bug, an
                # API case, a SQL case or a test case usually wants the
                # primary record of that type, not a requirement or an
                # exploratory note that merely mentions the same topic.
                if raw_tokens & {"bug", "defect", "bugs", "defects"}:
                    if doc_type == "bug_report":
                        final += 0.08
                if "api" in raw_tokens and doc_type == "api_test_case":
                    final += 0.08
                if "sql" in raw_tokens and doc_type == "sql_test_case":
                    final += 0.08
                if {"test", "case"} <= raw_tokens and doc_type in (
                    "test_case", "api_test_case", "sql_test_case",
                ):
                    final += 0.04
                if raw_tokens & {"risk", "risks", "plan"} and doc_type == "document":
                    final += 0.05
            results.append(
                {"chunk": chunk, "score": final, "vector_score": vector_score}
            )
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]
