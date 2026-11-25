# QA Knowledge Platform - Hugging Face Spaces (Docker SDK) / any Docker host
# Free CPU tier friendly: CPU-only torch, embedding model baked into the
# image at build time so first start does not download anything.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf \
    EMBEDDING_PROVIDER=auto \
    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

WORKDIR /app

# Dependencies first, for layer caching.
# torch is installed CPU-only from the PyTorch CPU index; the default
# PyPI wheel would pull several GB of CUDA libraries the free tier
# cannot use. Version pins match the local .venv that passed all tests
# (torch 2.15.0+cpu, sentence-transformers 6.3.0, fastapi 0.165.0,
# uvicorn 0.54.0, openpyxl 3.1.5).
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install "torch==2.15.0" --index-url https://download.pytorch.org/whl/cpu \
 && pip install "sentence-transformers==6.3.0" "fastapi==0.165.0" \
      "uvicorn==0.54.0" "openpyxl==3.1.5" numpy pydantic pytest

# Pre-download the embedding model into the image (stored under HF_HOME).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Application code and data. output/ carries the prebuilt chunks and
# search index (about 1 MB), so startup never re-runs ingestion or
# embedding; src/ingest.py and src/embed_index.py stay available in the
# image if a rebuild is ever needed.
COPY src/ ./src/
COPY web/ ./web/
COPY data/ ./data/
COPY output/ ./output/

EXPOSE 7860

# Same module layout as local runs: app.py inserts src/ into sys.path
# itself, and project-root paths (web/, output/) resolve from /app.
CMD ["uvicorn", "app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "7860"]
