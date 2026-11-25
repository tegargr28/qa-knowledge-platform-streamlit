"""Shared ask path for the Streamlit front end (streamlit_app.py).

This module contains NO Streamlit imports, so the exact function the
app calls on every question can also be imported by tests and by
eval/check_streamlit_pipeline.py.

It is a thin wrapper over ask.ask_question() — the same function the
FastAPI POST /ask endpoint and the CLI call. Nothing about retrieval,
the relevance threshold, the grounding rescue, answer composition or
citation validation is reimplemented here.

BYOK handling differs from the FastAPI version in one deliberate way:
the settings come from the caller's dict (in the app, the visitor's
own st.session_state) and are passed to ask_question() as
llm_overrides. llm.load_config() resolves explicit overrides BEFORE
environment variables and BEFORE the local settings file, so as long
as a provider is always present in the overrides, no key is ever read
from or written to a file on the server. That matters on Streamlit
Cloud, where one hosted process serves many visitors: a key typed by
one visitor must live only in that visitor's session, never on disk.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ask import ask_question  # noqa: E402

# The app's default session settings: the same default the FastAPI
# version ships with (extractive, no key, no model).
DEFAULT_SETTINGS = {
    "provider": "extractive",
    "api_key": "",
    "model": "",
    "base_url": "",
}


def build_overrides(settings):
    """Turn a settings dict into ask_question() llm_overrides.

    Mirrors the CLI in ask.py: empty values are dropped so they do not
    shadow anything, but the provider is always present (defaulting to
    "extractive"), which is what keeps llm.load_config() from ever
    falling through to a settings file for the provider choice.
    """
    settings = {**DEFAULT_SETTINGS, **(settings or {})}
    overrides = {
        "provider": settings.get("provider") or "extractive",
        "api_key": settings.get("api_key") or "",
        "model": settings.get("model") or "",
        "base_url": settings.get("base_url") or "",
    }
    return {k: v for k, v in overrides.items() if v}


def answer_question(question, project="all", settings=None, retriever=None):
    """Run one question through the shared pipeline.

    Returns exactly the dict ask.ask_question() returns:
    {answer, sources, citations_valid, provider, model, refused,
     top_score, grounding, list_mode}.
    """
    return ask_question(
        question,
        project=project,
        retriever=retriever,
        llm_overrides=build_overrides(settings),
    )
