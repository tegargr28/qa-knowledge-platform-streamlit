"""LLM gateway for the QA Knowledge Platform (Tahap 2).

Bring your own key (BYOK): this project ships with NO API key and NO
default paid model. Each user plugs in their own provider, key and
model. One module decides how an answer is produced, so the rest of
the app (retriever, validator, API) never changes when the provider
changes.

Configuration, in the order it is resolved (first hit wins):
1. Explicit overrides (CLI --provider/--model/--base-url, or the
   overrides argument of answer()).
2. Environment variables: LLM_PROVIDER, LLM_API_KEY, LLM_MODEL,
   LLM_BASE_URL (see .env.example).
3. The local settings file config/llm_settings.json, written by the
   POST /settings/llm endpoint. That file holds the user's own key on
   their own machine. It is listed in .gitignore and its key value is
   never returned by any endpoint, never printed, never logged here.
4. Defaults: provider "extractive", no key, no model.

Providers (adding one later means adding one small function and one
line in PROVIDERS; nothing else changes):
- "extractive": default. No key, no internet, no language model. It
  composes the answer only from the retrieved chunks, quoting their
  fields with citations. Honest and checkable, but it reads like a
  document excerpt.
- "openai-compatible": any endpoint that speaks the OpenAI
  chat-completions format. OpenAI, Groq, Together, OpenRouter, a local
  LM Studio server and many others are all covered by this one
  provider; only LLM_BASE_URL, LLM_API_KEY and LLM_MODEL change.
- "gemini": Google Gemini native API (its request format differs).
- "anthropic": Claude native API (its request format differs).
- "ollama": a local Ollama server. No key needed.

For every real model provider the prompt is strict: answer only from
the provided context, cite the document ID for every claim in the form
[project:doc_id], and if the context does not contain the answer say
exactly that it was not found in the documents. Whichever provider
answers, the citations are checked by validator.py in the same way.

If a model provider is configured but its key is missing (or ollama is
not reachable), the gateway falls back to extractive and says so in
the result instead of failing silently.
"""

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / "config" / "llm_settings.json"

NOT_FOUND = "The answer was not found in the documents."

_PRIORITY_FIELDS = [
    "Title / Summary", "Test Case Title", "Feature", "Steps to Reproduce",
    "Test Steps", "Expected Result", "Actual Result", "Actual Result / Observation",
    "Severity", "Priority", "Status", "Objective",
]
_TOKEN_RE = re.compile(r"[a-z0-9]+")


# ---------------------------------------------------------------- config

class LLMConfig:
    def __init__(self, provider="extractive", api_key="", model="",
                 base_url=""):
        self.provider = (provider or "extractive").lower()
        self.api_key = api_key or ""
        self.model = model or ""
        self.base_url = (base_url or "").rstrip("/")

    def public(self):
        """Settings as an API may show them: never the key value."""
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "key_set": bool(self.api_key),
        }


def _read_settings_file():
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(values):
    """Write the local settings file. values may include api_key.

    Returns the public (masked) view. The file itself is gitignored.
    """
    current = _read_settings_file()
    for field in ("provider", "api_key", "model", "base_url"):
        if values.get(field) is not None:
            current[field] = values[field]
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return load_config().public()


def load_config(overrides=None):
    overrides = overrides or {}
    saved = _read_settings_file()

    def pick(field, env_name):
        if overrides.get(field):
            return overrides[field]
        if os.environ.get(env_name):
            return os.environ[env_name]
        return saved.get(field, "")

    return LLMConfig(
        provider=pick("provider", "LLM_PROVIDER") or "extractive",
        api_key=pick("api_key", "LLM_API_KEY"),
        model=pick("model", "LLM_MODEL"),
        base_url=pick("base_url", "LLM_BASE_URL"),
    )


# ---------------------------------------------------------------- prompt

def build_prompt(question, chunks):
    """Strict prompt shared by every model provider.

    chunks: retriever results (dicts with a "chunk" key) or chunk dicts.
    """
    context_parts = []
    for item in chunks:
        chunk = item.get("chunk", item) if isinstance(item, dict) else item
        meta = chunk["metadata"]
        context_parts.append(
            f"[{meta['project']}:{meta['doc_id']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)
    return (
        "You answer questions about QA documents. Rules, no exceptions:\n"
        "1. Answer ONLY from the context below. Never use outside knowledge.\n"
        "2. Cite the document ID for every claim, in the form [project:doc_id], "
        "exactly as the context blocks are labelled.\n"
        f"3. If the context does not contain the answer, reply with exactly: "
        f"\"{NOT_FOUND}\"\n"
        "4. Keep the answer short and factual.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    )


# ---------------------------------------------------------------- extractive

def _fields_of(text):
    fields = []
    for part in text.split(" | "):
        if ": " in part:
            key, value = part.split(": ", 1)
            fields.append((key.strip(), value.strip()))
        elif part.strip():
            fields.append(("", part.strip()))
    return fields


def _keywords(text):
    return set(_TOKEN_RE.findall(text.lower()))


def extractive_answer(question, chunks, max_chunks=3):
    """Compose an answer from retrieved chunks only. No language model."""
    question_kw = _keywords(question)
    lines = ["Extractive answer (no LLM used, composed from the documents):"]
    used = 0
    for item in chunks:
        chunk = item.get("chunk", item) if isinstance(item, dict) else item
        meta = chunk["metadata"]
        citation = f"[{meta['project']}:{meta['doc_id']}]"
        fields = _fields_of(chunk["text"])
        picked = []
        for key, value in fields:
            if key in _PRIORITY_FIELDS:
                picked.append((key, value))
            elif value and len(question_kw & _keywords(value)) >= 2:
                picked.append((key, value))
        if not picked and fields:
            picked = fields[:3]
        picked = picked[:6]
        if used == 0:
            for key, value in picked:
                label = f"{key}: " if key else ""
                lines.append(f"- {label}{value[:300]} {citation}")
        else:
            first = picked[0][1] if picked else chunk["text"][:200]
            lines.append(f"- Related: {first[:200]} {citation}")
        used += 1
        if used >= max_chunks:
            break
    return "\n".join(lines)


_ID_LIKE_RE = re.compile(r"\b(?:BUG|TC|FR|DB|API|EXEC|PAY|SCN|REQ)-[A-Z0-9]*\d")


def list_answer(question, chunks, max_items=14):
    """Extractive answer for list questions: enumerate the records.

    Bug/test-case records become one line each (ID + title). Document
    chunks that enumerate items (a README summary table, for example)
    contribute the lines that mention a record ID. Every line carries
    its citation, so the validator checks list answers the same way as
    any other answer.
    """
    lines = ["Extractive answer (no LLM used, composed from the documents):"]
    for item in chunks:
        chunk = item.get("chunk", item) if isinstance(item, dict) else item
        meta = chunk["metadata"]
        citation = f"[{meta['project']}:{meta['doc_id']}]"
        if meta.get("doc_type") == "document":
            item_lines = [
                ln.strip().strip("|").strip()
                for ln in chunk["text"].splitlines()
                if _ID_LIKE_RE.search(ln)
            ]
            for ln in item_lines[:max_items]:
                lines.append(f"- {ln[:300]} {citation}")
            if not item_lines:
                first = next(
                    (ln.strip() for ln in chunk["text"].splitlines()
                     if ln.strip()), "",
                )
                if first:
                    lines.append(f"- {first[:300]} {citation}")
        else:
            fields = _fields_of(chunk["text"])
            title = ""
            for key, value in fields:
                if key in ("Title / Summary", "Test Case Title", "Feature"):
                    title = value
                    break
            if not title and fields:
                title = fields[0][1]
            lines.append(f"- {meta['doc_id']}: {title[:250]} {citation}")
    return "\n".join(lines)


# ---------------------------------------------------------------- HTTP seam

def _post_json(url, payload, headers=None):
    """Single HTTP seam. Tests replace this; no real call is made there."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------- providers

def build_openai_request(config, question, chunks):
    """Build (url, headers, payload) for any OpenAI-compatible endpoint."""
    base = config.base_url or "https://api.openai.com/v1"
    url = base.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}"}
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": build_prompt(question, chunks)}],
    }
    return url, headers, payload


def _answer_openai_compatible(config, question, chunks):
    url, headers, payload = build_openai_request(config, question, chunks)
    data = _post_json(url, payload, headers=headers)
    return data["choices"][0]["message"]["content"].strip()


def _answer_gemini(config, question, chunks):
    model = config.model or "gemini-2.0-flash"
    base = config.base_url or "https://generativelanguage.googleapis.com/v1beta"
    url = f"{base.rstrip('/')}/models/{model}:generateContent?key={config.api_key}"
    data = _post_json(
        url, {"contents": [{"parts": [{"text": build_prompt(question, chunks)}]}]}
    )
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _answer_anthropic(config, question, chunks):
    model = config.model or "claude-3-5-sonnet-latest"
    base = config.base_url or "https://api.anthropic.com/v1"
    data = _post_json(
        base.rstrip("/") + "/messages",
        {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": build_prompt(question, chunks)}],
        },
        headers={
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    return data["content"][0]["text"].strip()


def _answer_ollama(config, question, chunks):
    model = config.model or "llama3.1"
    base = config.base_url or "http://localhost:11434"
    data = _post_json(
        base.rstrip("/") + "/api/chat",
        {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": build_prompt(question, chunks)}],
        },
    )
    return data["message"]["content"].strip()


# Providers that need an API key before they can run.
_KEY_REQUIRED = {"openai-compatible", "openai", "gemini", "anthropic"}

PROVIDERS = {
    "extractive": None,  # handled directly, needs no HTTP
    "openai-compatible": _answer_openai_compatible,
    "openai": _answer_openai_compatible,
    "gemini": _answer_gemini,
    "anthropic": _answer_anthropic,
    "claude": _answer_anthropic,
    "ollama": _answer_ollama,
}


def answer(question, chunks, overrides=None, list_mode=False):
    """Return {answer, provider, model, fell_back}.

    Falls back to extractive (and says so) when the configured model
    provider has no key or the call fails. list_mode only changes the
    extractive composition: the answer enumerates the retrieved
    records instead of quoting the top ones. Model providers receive
    the same retrieved chunks as context either way.
    """
    config = load_config(overrides)
    provider = config.provider
    fn = PROVIDERS.get(provider)
    if provider != "extractive" and fn is not None:
        if provider in _KEY_REQUIRED and not config.api_key:
            pass  # fall through to extractive below
        else:
            try:
                text = fn(config, question, chunks)
                return {
                    "answer": text,
                    "provider": provider,
                    "model": config.model or "(provider default)",
                    "fell_back": False,
                }
            except Exception:
                pass  # fall through to extractive below
    text = (
        list_answer(question, chunks) if list_mode
        else extractive_answer(question, chunks)
    )
    return {
        "answer": text,
        "provider": "extractive",
        "model": "none (document excerpts only)",
        "fell_back": provider != "extractive",
    }
