"""Build the local vector index (Tahap 2).

Reads output/chunks.jsonl from Tahap 1, embeds every chunk text with the
provider from embeddings.py, and saves a simple transparent index:

    output/index/vectors.npy     float32 matrix, one row per chunk
    output/index/chunks_meta.json  chunk id, text and metadata, same order
    output/index/index_info.json   provider, model, dimension, counts
    output/index/tfidf_state.json  only when the TF-IDF fallback was used

No server is involved. The retriever only depends on these files, so a
real vector database (pgvector or Qdrant, see docs/DESIGN.md) can take
over later without touching the rest of the code.

Run:  python src/embed_index.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import embeddings

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = ROOT / "output" / "chunks.jsonl"
INDEX_DIR = ROOT / "output" / "index"


def main():
    chunks = [
        json.loads(line)
        for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    texts = [c["text"] for c in chunks]
    provider, fell_back = embeddings.get_provider(corpus_texts=texts)
    vectors = provider.embed_texts(texts)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_DIR / "vectors.npy", vectors)
    meta = [
        {"id": c["id"], "text": c["text"], "metadata": c["metadata"]}
        for c in chunks
    ]
    (INDEX_DIR / "chunks_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    if provider.name == "tfidf":
        (INDEX_DIR / "tfidf_state.json").write_text(
            json.dumps(provider.state()), encoding="utf-8"
        )
    info = {
        "provider": provider.name,
        "model": provider.model_name,
        "fell_back_to_tfidf": fell_back,
        "dimension": int(vectors.shape[1]),
        "chunk_count": int(vectors.shape[0]),
        "projects": sorted({c["metadata"]["project"] for c in chunks}),
    }
    (INDEX_DIR / "index_info.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    print(json.dumps(info, indent=2))
    return info


if __name__ == "__main__":
    main()
