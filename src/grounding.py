"""Grounding check for the QA Knowledge Platform (Tahap 3 fix).

The relevance score alone cannot separate real questions from trap
questions: on the 25 golden questions the answerable top scores run
0.590 to 0.966 and the trap top scores 0.497 to 0.644, so any single
threshold either lets traps through or refuses real questions.

This module adds a second, independent signal: are the question's own
distinctive words actually present in the retrieved text? A real
question about a real record shares its vocabulary with that record
("quantity", "stock" for the over-stock bug). A trap question asks
about things the documents never mention ("CEO", "salary", "OTP",
"sms", "refund", "credit card"), so its distinctive words are absent
from whatever chunks happen to be retrieved.

Terms are weighted by rarity across the whole corpus: a term that
appears in few chunks (idf-style weight) counts more than a term that
appears everywhere. Two coverage numbers are produced over the top 3
retrieved chunks:

- weighted_union: fraction of the question's term weight covered by
  the top 3 chunks taken together.
- weighted_best: the same fraction for the single best chunk. A trap
  can look covered when its words are scattered across unrelated
  chunks (a "password" chunk here, a "database" chunk there); a real
  question usually has one record that covers most of its words.

Measured on the 25 golden questions (see reports/eval_report.md):
real but low-scoring questions reach weighted_union 0.68 and
weighted_best 0.50, while every trap stays at or below 0.53 / 0.35.
ask.py uses rescue limits of 0.60 and 0.45, between those groups.
"""

import math
import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Function words plus words that appear in almost every QA question
# and so carry no signal about which record is being asked about.
# This is the exact set the calibration in reports/eval_report.md was
# measured with; changing it changes the measured numbers.
_STOPWORDS = {
    "the", "a", "an", "what", "which", "how", "many", "much", "when",
    "why", "who", "is", "are", "was", "were", "does", "do", "did",
    "in", "on", "of", "for", "to", "with", "by", "at", "after",
    "before", "during", "while", "it", "its", "their", "them", "they",
    "user", "users",
    "bug", "bugs", "defect", "defects", "test", "tests", "case",
    "cases", "report", "reports", "found", "application", "app",
    "demo", "executed", "executing", "session", "flow",
}


def _stem(token):
    """Very small stemmer: orders -> order, risks -> risk."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _terms(text):
    seen = []
    for token in _TOKEN_RE.findall((text or "").lower()):
        if token in _STOPWORDS or len(token) <= 1:
            continue
        term = _stem(token)
        if term not in seen:
            seen.append(term)
    return seen


class GroundingModel:
    """Corpus statistics needed to score how grounded a question is."""

    def __init__(self, chunks):
        self.n_chunks = len(chunks)
        self.chunk_terms = []
        doc_freq = {}
        for chunk in chunks:
            terms = set(_terms(chunk.get("text", "")))
            self.chunk_terms.append(terms)
            for term in terms:
                doc_freq[term] = doc_freq.get(term, 0) + 1
        self._weights = {
            term: math.log((self.n_chunks + 1) / (df + 0.5))
            for term, df in doc_freq.items()
        }
        # A term that never appears in the corpus is the rarest of all.
        self._unseen_weight = math.log(self.n_chunks + 1)

    def weight(self, term):
        return self._weights.get(term, self._unseen_weight)

    def assess(self, question, results, top_n=3):
        """Grounding of a question in its top retrieved chunks.

        results: retriever result dicts (with a "chunk" key holding the
        chunk's corpus position is NOT available, so chunk texts are
        read directly from the result dicts).
        """
        terms = _terms(question)
        total = sum(self.weight(t) for t in terms) or 1.0
        top = list(results or [])[:top_n]
        covered_union = set()
        best = 0.0
        for item in top:
            chunk = item.get("chunk", item) if isinstance(item, dict) else item
            chunk_terms = set(_terms(chunk.get("text", "")))
            covered = {t for t in terms if t in chunk_terms}
            covered_union |= covered
            best = max(best, sum(self.weight(t) for t in covered) / total)
        union = sum(self.weight(t) for t in covered_union) / total
        return {
            "weighted_union": round(union, 4),
            "weighted_best": round(best, 4),
            "terms": terms,
            "covered_terms": sorted(covered_union),
        }
