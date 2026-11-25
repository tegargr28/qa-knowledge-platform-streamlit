# Deploy notes (packaging only, nothing deployed yet)

Primary route: Hugging Face Spaces, Docker SDK, free CPU tier.
Chosen because it needs no card on file. Render, Fly.io and Railway
were ruled out earlier in this project family because they ask for a
card even on free tiers, and Tegar has none.

## Later steps, in order (each needs Tegar's approval at the time)

1. Create a Hugging Face account if Tegar does not have one yet
   (huggingface.co, free, email signup, no card).
2. Create a new Space: SDK = Docker, hardware = CPU basic (free).
3. Put the Space README in place: copy deploy/hf-spaces-README.md to
   the Space repo root as README.md. Its YAML front matter (sdk:
   docker, app_port: 7860) is what tells HF how to run the Space. The
   GitHub repo keeps its own long README.md; the two files are
   deliberately separate.
4. Upload or push the publish set from the GitHub repo (same file list
   as reports/publication_audit.md). The Dockerfile at the repo root
   is what HF builds.
5. Set NO secrets in the Space settings. The app is bring-your-own-key
   by design: it ships with no API key, answers in extractive mode out
   of the box, and any user who wants a model answer enters their own
   key in the app's settings panel.
6. First start behaviour: the Docker build downloads CPU torch and the
   embedding model (all-MiniLM-L6-v2, about 90 MB) and bakes the model
   into the image, so the running Space does not download anything.
   The prebuilt search index ships in output/ (about 1 MB), so there
   is no ingestion or embedding rebuild at startup. First question may
   still take some seconds while the model loads into memory on CPU.

## Free tier limits, stated honestly

- The Space sleeps after a period without visitors; the next visit
  wakes it and takes noticeably longer.
- CPU only. Extractive answers are fine at this speed because they
  only embed the question and search 321 chunks. Rebuilding the whole
  index on CPU is the slow part, which is why the prebuilt index is
  shipped instead.
- The Docker image is not small: python slim plus CPU torch plus the
  model lands roughly in the 1.5 to 2.5 GB range. Builds on HF will
  take a while. This was not measured with a real build yet (no Docker
  on the build machine, see the publication audit); treat the range as
  an estimate, not a result.

## If Hugging Face does not work out

- Run it locally, which already works and is fully tested:
  .venv/bin/uvicorn app:app --app-dir src --port 8000
  then open http://localhost:8000/ for the chat page.
- Any Docker host that does not demand a card can use the same
  Dockerfile unchanged (it only assumes port 7860 is reachable; the
  port can be changed in the CMD line).
- A plain GitHub repo release still stands on its own: the eval
  reports and the chat page run locally are the portfolio evidence,
  the Space is only the public demo.
