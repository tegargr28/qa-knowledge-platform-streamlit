# Streamlit version - notes

This copy of the QA Knowledge Platform adds a Streamlit front end so
the app can be hosted on Streamlit Community Cloud (free, no card).
The FastAPI version in the same repo (src/app.py + web/index.html) is
unchanged and still works locally. Nothing here has been pushed or
deployed yet; this file records what was built and verified locally,
and the exact deploy steps for later.

## What changed vs the FastAPI version, and why

Added:
- `streamlit_app.py` (repo root): the Streamlit chat page. Indonesian
  labels and texts mirror web/index.html: same header line, same
  project picker (Semua Project / ParaBank / Chaligula), same
  greeting, same sources block ("Sumber:", [project:doc_id], sheet,
  score), same citation-check note, same refusal text plus the same
  refusal explanation line, same footer note.
- `src/streamlit_core.py`: a thin, Streamlit-free wrapper. Its
  `answer_question()` is the exact function the app calls per
  question; it forwards to `ask.ask_question()` with the visitor's
  settings as `llm_overrides`. No pipeline logic lives here.
- `eval/check_streamlit_pipeline.py` + its report
  `reports/streamlit_pipeline_check.md`: the behaviour check below.
- This file.

Changed (in this copy only):
- `requirements.txt`: now the Streamlit Cloud requirements (see
  below). The original file stays in the FastAPI project; the
  Dockerfile route is unaffected.
- `.gitignore`: one added line, `.venv-streamlit/` (the local test
  environment used for verification here).

Not changed: everything else is a byte-for-byte copy of the published
project, including src/ask.py, src/retriever.py, src/grounding.py,
src/validator.py, src/llm.py, the prebuilt index in output/, the
golden questions and the test suite. The pipeline is reused, not
reimplemented: retrieval, the 0.65 relevance threshold, the grounding
rescue, list-question handling, answer composition and citation
validation all run in the original modules.

## The one deliberate behaviour difference: BYOK settings storage

The FastAPI version persists LLM settings to
config/llm_settings.json on the user's own machine (single user).
That design is wrong for a hosted multi-visitor app: one visitor's
API key must never be written to a shared server's disk or be visible
to another visitor.

So in the Streamlit app the BYOK settings (provider, base URL, model,
API key) live only in `st.session_state`:
- They are passed to the pipeline as explicit overrides, which
  llm.load_config() resolves before environment variables and before
  any settings file, so no file is read for them and none is written.
- The key field is a password input; the key is never displayed back
  (the sidebar shows only "sudah terisi / belum terisi").
- The settings die with the visitor's session.
Default is unchanged: provider extractive, no key, answers composed
from the documents.

## Verification (all local, 2026-11-26)

Environment: a fresh venv (.venv-streamlit/, excluded from the
publishable set) with torch 2.15.0+cpu, sentence-transformers 6.3.0,
streamlit 1.67.0, numpy 2.5.5, openpyxl 3.1.5 - the same versions as
the FastAPI project's environment, plus Streamlit.

- Pipeline behaviour: `eval/check_streamlit_pipeline.py` ran all 25
  golden questions through streamlit_core.answer_question() (the
  app's own function) with the app's default settings, scored with
  run_eval.py's rules. Result: **25/25 - answerable 20/20, traps
  refused 5/5.** Same as the FastAPI pipeline. Report:
  reports/streamlit_pipeline_check.md.
- Existing test suite in this copy: **31 passed** (run with the
  project venv interpreter, which has the full dependency set). Note:
  run inside .venv-streamlit alone, 29 pass, 1 is skipped and 1 fails
  at import, both only because that venv deliberately has no
  fastapi/httpx - the two FastAPI-endpoint tests cannot import
  src/app.py there. That is an environment artifact of the slim
  Streamlit venv, not a code failure; with the full dependency set
  all 31 pass.
- Live app test: `streamlit run streamlit_app.py --server.headless
  true --server.port 8501` served HTTP 200 with a clean log.
  Separately, Streamlit's AppTest ran the real script end to end: the
  initial run loaded model + index and rendered the greeting and the
  "321 potongan dokumen terindeks" line; a chat question about
  over-stock orders in Chaligula was answered citing
  [chaligula:BUG-001] with the sources block; the trap "Who is the
  CEO of ParaBank?" was refused with the not-found message. No
  exceptions in any run.
- Memory (steady state): measured with AppTest, which runs the app
  in one Python process, reading that process's VmRSS from
  /proc/self/status. RSS was 46 MB before the app ran, 528 MB after
  the initial run (Streamlit runtime + torch + embedding model +
  index loaded), 579 MB after answering one question, and **581 MB
  at the end (steady state)**. Streamlit Community Cloud's free tier
  is documented at roughly 1 GB guaranteed and up to about 2.7 GB of
  RAM per app, so 581 MB fits with headroom. Caveat: this is the app
  process measured on this machine; the hosted container adds its own
  platform overhead, and the exact free-tier ceiling is not a hard
  published number, so treat the fit as plausible and verified
  locally, not guaranteed.
- Secret scan of the publishable files (excluding the venvs and
  caches): no config/ directory exists in this copy, no
  llm_settings.json, and no real-format keys or tokens (sk-, hf_,
  AKIA, ghp_, private keys, assigned secrets) were found. The only
  key-like strings are the previously audited, obviously dummy test
  keys in tests/test_tahap2.py.

## requirements.txt approach (Streamlit Cloud)

```
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.15.0+cpu
streamlit==1.67.0
sentence-transformers==6.3.0
numpy==2.5.5
openpyxl==3.1.5
```

The extra index adds the PyTorch CPU wheel index and the
`torch==2.15.0+cpu` pin can only be satisfied from there, so the
build installs the CPU-only wheel (~200 MB) instead of the multi-GB
CUDA wheel plain PyPI would pull. fastapi/uvicorn/pytest are omitted:
the Streamlit entry point does not import them (local dev tools and
the unused-on-Cloud FastAPI module aside).

## Deploy steps (for later, each needs approval at the time)

1. Push this copy to its own GitHub repository (a new repo, e.g.
   tegargr28/qa-knowledge-platform-streamlit; the FastAPI repo stays
   as it is). Publishable set: the files in this folder except
   .venv-streamlit/, .cache/, __pycache__/, .pytest_cache/ - the same
   exclusions as .gitignore. Do not publish the local model cache in
   .cache/; the hosted app downloads the embedding model
   (all-MiniLM-L6-v2, about 90 MB) from Hugging Face on first start.
2. Go to https://share.streamlit.io and sign in with GitHub
   (tegargr28). No card is asked for the free Community Cloud.
3. "Create app" -> deploy a public app from GitHub: repository = the
   new repo, branch = main, main file path = `streamlit_app.py`.
4. Advanced settings: Python 3.12. No secrets are needed - the app is
   bring-your-own-key by design and ships with none.
5. First start will install requirements (CPU torch), download the
   embedding model once, then load the prebuilt index from output/.
   Expect the first question to take some seconds while the model
   warms up. The app sleeps after a period without visitors on the
   free tier; the next visit wakes it.

## Honest limitations

- The real Streamlit Cloud build has NOT been run. Everything above
  was verified locally in an equivalent venv. Cloud-specific risks
  that remain unproven: the exact install time of the CPU torch
  wheel, the model download on first start, and the platform's exact
  memory ceiling behaviour under its own overhead.
- The hosted app's first visitor pays the model-load cost (the model
  is not baked into anything on Streamlit Cloud, unlike the Docker
  image in the FastAPI route).
- BYOK providers other than extractive were not re-tested through the
  Streamlit UI (the gateway code is unchanged and covered by the
  existing test suite; the AppTest run used the default extractive
  provider, same as the eval).
