"""FastAPI service for the QA Knowledge Platform (Tahap 3).

Endpoints:
    GET  /              -> the simple chat page (web/index.html, one
                           self-contained file, no build step, no CDN)
    GET  /health        -> status, indexed chunk count, active providers
    POST /ask           -> {question, project?} returns
                           {answer, sources: [{doc_id, project, sheet, score}],
                            citations_valid, provider}
    GET  /settings/llm  -> current LLM provider, base URL, model and
                           whether a key is set. The key value itself is
                           NEVER returned.
    POST /settings/llm  -> {provider?, api_key?, model?, base_url?}
                           stores the user's own settings in the local
                           file config/llm_settings.json (gitignored).
                           Bring your own key: the app ships with none.

Run:  uvicorn app:app --app-dir src --port 8000
Personal mode: no login, every project allowed (see ask.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import llm
from ask import ask_question
from retriever import Retriever

ROOT = Path(__file__).resolve().parent.parent
INDEX_PAGE = ROOT / "web" / "index.html"

app = FastAPI(title="QA Knowledge Platform", version="0.3.0")
_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


class AskRequest(BaseModel):
    question: str
    project: str = "all"


class LLMSettingsRequest(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None


@app.get("/")
def chat_page():
    return FileResponse(INDEX_PAGE, media_type="text/html")


@app.get("/health")
def health():
    retriever = get_retriever()
    return {
        "status": "ok",
        "chunks_indexed": len(retriever.chunks),
        "embedding_provider": retriever.info["provider"],
        "embedding_model": retriever.info["model"],
        "llm": llm.load_config().public(),
    }


@app.post("/ask")
def ask(req: AskRequest):
    return ask_question(req.question, project=req.project, retriever=get_retriever())


@app.get("/settings/llm")
def get_llm_settings():
    return llm.load_config().public()


@app.post("/settings/llm")
def post_llm_settings(req: LLMSettingsRequest):
    saved = llm.save_settings(req.model_dump())
    return saved
