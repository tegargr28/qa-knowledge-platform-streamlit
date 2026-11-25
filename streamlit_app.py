"""Streamlit front end for the QA Knowledge Platform.

Same pipeline as the FastAPI version (src/app.py + web/index.html):
every question goes through streamlit_core.answer_question(), which
calls ask.ask_question() — the shared retriever, relevance threshold,
grounding rescue, answer composition and citation validation. Only
the page around it is Streamlit instead of hand-written HTML.

Differences from the FastAPI version, all deliberate:
- BYOK settings live ONLY in st.session_state. The hosted app serves
  many visitors from one process, so a key must never be written to a
  file on the server (the FastAPI version's config/llm_settings.json
  is a single-user, own-machine design). The key is never displayed
  back, and it disappears when the visitor's session ends.
- The embedding model and the prebuilt index in output/ are loaded
  once per process via st.cache_resource and shared across sessions;
  the model itself is read-only after loading.

Run locally:  streamlit run streamlit_app.py
On Streamlit Cloud this file is the app entry point (see
STREAMLIT_NOTES.md).
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import llm  # noqa: E402
from retriever import Retriever  # noqa: E402
from streamlit_core import DEFAULT_SETTINGS, answer_question  # noqa: E402

st.set_page_config(page_title="QA Knowledge Platform", page_icon="🔎")

PROVIDER_OPTIONS = {
    "extractive": "extractive (tanpa kunci, kutip dokumen)",
    "openai-compatible": "openai-compatible (OpenAI, Groq, OpenRouter, LM Studio, dll.)",
    "gemini": "gemini",
    "anthropic": "anthropic",
    "ollama": "ollama (lokal, tanpa kunci)",
}

PROJECT_OPTIONS = {
    "all": "Semua Project",
    "parabank": "ParaBank",
    "chaligula": "Chaligula",
}

GREETING = (
    "Halo. Silakan tanya soal test case, bug, atau dokumen QA dari "
    "ParaBank dan Chaligula. Kalau jawabannya tidak ada di dokumen, "
    "sistem akan bilang tidak ditemukan, bukan mengarang."
)

REFUSAL_NOTE = (
    "(Tidak ditemukan di dokumen. Sistem menolak menjawab dari "
    "potongan yang relevansinya terlalu lemah.)"
)


@st.cache_resource(show_spinner="Memuat model dan index dokumen...")
def load_retriever():
    """Load the prebuilt index and embedding model once per process."""
    return Retriever()


def current_settings():
    """BYOK settings from this visitor's session only. Never on disk."""
    return {
        "provider": st.session_state.get("byok_provider", DEFAULT_SETTINGS["provider"]),
        "api_key": st.session_state.get("byok_api_key", ""),
        "model": st.session_state.get("byok_model", ""),
        "base_url": st.session_state.get("byok_base_url", ""),
    }


def render_message(msg):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("refused"):
            st.warning(msg["text"])
            st.caption(REFUSAL_NOTE)
        else:
            st.markdown(msg["text"])
        if msg["role"] == "assistant" and not msg.get("refused") and msg.get("sources"):
            st.markdown("**Sumber:**")
            for s in msg["sources"]:
                st.markdown(
                    f"- [{s['project']}:{s['doc_id']}] sheet: "
                    f"{s['sheet'] or '-'}, skor {s['score']}"
                )
            if msg.get("citations_valid"):
                st.caption(
                    "Sitasi jawaban ini sudah diperiksa dan cocok dengan "
                    f"sumber di atas. Penyedia: {msg.get('provider', '')}"
                )
            else:
                st.caption(
                    "Perhatian: sitasi jawaban ini tidak lolos "
                    f"pemeriksaan. Penyedia: {msg.get('provider', '')}"
                )


# ---------------------------------------------------------------- sidebar

with st.sidebar:
    st.subheader("Pengaturan Model AI (bawa kunci sendiri / BYOK)")
    st.selectbox(
        "Penyedia (provider)",
        options=list(PROVIDER_OPTIONS),
        format_func=lambda p: PROVIDER_OPTIONS[p],
        key="byok_provider",
    )
    st.text_input(
        "Base URL (untuk openai-compatible dan ollama)",
        placeholder="misalnya https://api.groq.com/openai/v1",
        key="byok_base_url",
    )
    st.text_input(
        "Nama model",
        placeholder="misalnya llama-3.3-70b-versatile",
        key="byok_model",
    )
    st.text_input(
        "API key kamu sendiri (tidak pernah ditampilkan kembali)",
        type="password",
        placeholder="Hanya tersimpan di sesi ini",
        key="byok_api_key",
    )
    _settings = current_settings()
    st.caption(
        f"Status sekarang: provider {_settings['provider']}, model "
        f"{_settings['model'] or '(bawaan provider)'}, kunci "
        f"{'sudah terisi' if _settings['api_key'] else 'belum terisi'}. "
        "Pengaturan hanya tersimpan di sesi browser ini dan hilang "
        "saat sesi berakhir; tidak ada yang ditulis ke server."
    )

# ---------------------------------------------------------------- main

st.title("QA Knowledge Platform")
st.caption(
    "Tanya jawab atas dokumen QA ParaBank dan Chaligula. Setiap "
    "jawaban menyebut sumbernya dan sitasinya diperiksa."
)

retriever = load_retriever()
st.caption(f"Index siap: {len(retriever.chunks)} potongan dokumen terindeks.")

project_label = st.selectbox(
    "Pilih project",
    options=list(PROJECT_OPTIONS),
    format_func=lambda p: PROJECT_OPTIONS[p],
    key="project",
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "text": GREETING, "sources": [],
         "citations_valid": True, "provider": "", "refused": False}
    ]

for msg in st.session_state.messages:
    render_message(msg)

question = st.chat_input(
    "Tulis pertanyaanmu, misalnya: bug apa yang terjadi saat login "
    "dengan password salah?"
)

if question:
    st.session_state.messages.append({"role": "user", "text": question})
    render_message(st.session_state.messages[-1])
    with st.spinner("Mencari di dokumen..."):
        out = answer_question(
            question,
            project=st.session_state.get("project", "all"),
            settings=current_settings(),
            retriever=retriever,
        )
    refused = bool(out.get("refused")) or out["answer"] == llm.NOT_FOUND
    reply = {
        "role": "assistant",
        "text": out["answer"],
        "sources": [] if refused else out["sources"],
        "citations_valid": out["citations_valid"],
        "provider": out["provider"],
        "refused": refused,
    }
    st.session_state.messages.append(reply)
    render_message(reply)

st.caption(
    "Mode perorangan: tanpa login, semua project boleh diakses oleh "
    "pemiliknya. Versi perusahaan memakai login dan izin per project "
    "(lihat docs/DESIGN.md)."
)
