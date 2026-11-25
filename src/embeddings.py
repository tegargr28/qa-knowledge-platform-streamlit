"""Embedding layer for the QA Knowledge Platform (Tahap 2).

Everything that needs vectors goes through this interface:

    provider.embed_texts(list_of_texts) -> 2D numpy array, L2 normalised
    provider.embed_query(text)          -> 1D numpy array, L2 normalised

Providers:
- "st"    : local sentence-transformers model (default
            sentence-transformers/all-MiniLM-L6-v2). No API key, runs on
            this machine. The model is cached under .cache/hf in the
            project so it survives machine restarts.
- "tfidf" : TF-IDF fallback written with plain numpy. Clearly weaker
            than a real embedding model (it matches words, not meaning),
            but it needs no download at all. It has to be fit on the
            corpus first, and its vocabulary is saved next to the index.

Selection: EMBEDDING_PROVIDER env var. "auto" (default) tries the local
sentence-transformers model first and falls back to TF-IDF if the model
cannot be loaded. The provider that actually ran is recorded in the
index metadata, never assumed.
"""

import os
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Keep model downloads inside the project (home persists, /tmp is small).
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "hf"))
os.environ.setdefault("TMPDIR", str(ROOT / ".cache" / "tmp"))


def _normalise(matrix):
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class SentenceTransformerProvider:
    name = "sentence-transformers"

    def __init__(self, model_name=DEFAULT_ST_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        vectors = self.model.encode(
            list(texts), batch_size=32, show_progress_bar=False,
            convert_to_numpy=True,
        )
        return _normalise(vectors)

    def embed_query(self, text):
        return self.embed_texts([text])[0]


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text):
    return _TOKEN_RE.findall(text.lower())


class TFIDFProvider:
    """Plain numpy TF-IDF. Fallback only; matches words, not meaning."""

    name = "tfidf"

    def __init__(self, vocab=None):
        self.model_name = "tfidf-plain-numpy"
        self.vocab = vocab or {}
        self.idf = None
        if vocab:
            self.idf = np.zeros(len(vocab), dtype=np.float32)

    def fit(self, texts):
        docs = [_tokens(t) for t in texts]
        vocab = {}
        for doc in docs:
            for tok in set(doc):
                if tok not in vocab:
                    vocab[tok] = len(vocab)
        df = np.zeros(len(vocab), dtype=np.float32)
        for doc in docs:
            for tok in set(doc):
                df[vocab[tok]] += 1
        n = max(len(docs), 1)
        self.vocab = vocab
        self.idf = np.log((1 + n) / (1 + df)) + 1.0
        return self

    def _vectorise(self, texts):
        out = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for i, text in enumerate(texts):
            toks = _tokens(text)
            if not toks:
                continue
            for tok in toks:
                j = self.vocab.get(tok)
                if j is not None:
                    out[i, j] += 1.0
            out[i] *= self.idf
        return _normalise(out)

    def embed_texts(self, texts):
        if self.idf is None:
            raise RuntimeError("TFIDFProvider must be fit on the corpus first")
        return self._vectorise(texts)

    def embed_query(self, text):
        return self.embed_texts([text])[0]

    def state(self):
        return {"vocab": self.vocab, "idf": self.idf.tolist()}

    @classmethod
    def from_state(cls, state):
        provider = cls(vocab=state["vocab"])
        provider.idf = np.asarray(state["idf"], dtype=np.float32)
        return provider


def get_provider(requested=None, corpus_texts=None):
    """Return (provider, fell_back: bool). corpus_texts is used to fit TF-IDF."""
    choice = (requested or os.environ.get("EMBEDDING_PROVIDER") or "auto").lower()
    if choice in ("auto", "st", "sentence-transformers"):
        try:
            return SentenceTransformerProvider(
                os.environ.get("EMBEDDING_MODEL", DEFAULT_ST_MODEL)
            ), False
        except Exception:
            if choice != "auto":
                raise
    provider = TFIDFProvider()
    if corpus_texts is not None:
        provider.fit(corpus_texts)
    return provider, choice == "auto"
