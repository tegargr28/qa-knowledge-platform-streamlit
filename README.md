# QA Knowledge Platform

This is my AI Engineer portfolio project. I built it because my QA work
is spread over Excel workbooks and Markdown documents from two projects,
ParaBank and Chaligula QA, and finding an old bug or a test case means
opening files one by one. This project turns those documents into
something I can search by meaning and, in the next stages, ask questions
against with sources I can check.

The design is enterprise style: company, then projects, then members
with roles, with permission filtering before search and an audit log.
Right now it runs in personal mode, which is the same design with the
company size set to one. I am the only member and I hold every role, the
sources are my own files, and the enterprise features (SSO, company
connectors, private deployment) are designed in docs/DESIGN.md but not
built yet. I am not claiming any company uses this. The plan is personal
first, then usable by a small team, then enterprise requirements.

## Current status: Tahap 3, refusal, full answer evaluation and a chat page

Done and verified by running it:

- The system now refuses questions it cannot ground, and the refusal
  rule has two parts. If the best chunk the search finds scores at
  least 0.65, the question is answered. Below that, a grounding check
  looks at the question itself: are its distinctive words, weighted
  by how rare they are in the corpus, actually present in the
  retrieved text, both across the top three chunks and in one single
  chunk? A real question shares its words with its record, a trap
  question asks about things the documents never mention. The check
  runs before any model provider is called, so it holds for every
  provider. The first version used the score alone and refused two
  real questions along with the traps; the grounding check is what
  fixed that, and the measured numbers for both groups are in
  reports/eval_report.md.
- A golden set of 25 questions now scores the full pipeline, answers
  included, not only the search. Twenty questions are answerable from
  my documents; five are traps whose only correct behaviour is
  refusal (the CEO of ParaBank, a production database password, a bug
  in a forgot-password SMS flow that does not exist in my data, a
  credit card refund bug that does not exist, the QA team's salary).
  First full run: 22 of 25 passed (88%). After the fix above, plus
  general handling for list questions (a wider search, the records of
  the type asked for, and the project document that lists those same
  records as a source), the current run is 25 of 25 (100%), gate
  passes, all five traps still refused. The honest limit: the two
  rescued questions sit close to the rescue limits, so the rule is
  calibrated on this set of 25 and would need re-measuring on a
  bigger set before I would call it robust. Full table in
  reports/eval_report.md.
- The Tahap 2 retrieval numbers did not move: Hit@1 7/12 (58%),
  Hit@5 11/12 (92%) on the original 12 questions.
- There is a simple chat page at GET / when the API runs. It is one
  self-contained HTML file with Indonesian labels, a project picker
  (Semua, ParaBank, Chaligula), the answer with its sources and a
  note on whether the citations were checked, and a settings panel
  for the bring-your-own-key model settings. The key field is never
  prefilled, because the server never sends a stored key back.
- Thirty-one pytest tests pass: the eleven from Tahap 1 and 2, the
  Tahap 3 tests for the threshold, trap refusal and the chat page,
  and tests for the grounding rescue (a low score with strong
  grounding is allowed, scattered words across unrelated chunks do
  not rescue a question), for list detection in English and
  Indonesian, and for the three fixed questions through the real
  pipeline.

## Tahap 2, search and question answering

- All 321 chunks from Tahap 1 are embedded with a local model,
  sentence-transformers/all-MiniLM-L6-v2, running on this machine.
  No API key is needed for search. The vectors and their metadata sit
  in output/index/ as plain files, behind a retriever interface, so a
  real vector database can take over later without touching the rest
  of the code.
- The retriever applies the project filter and the permission filter
  before ranking, as the design asks. In personal mode every project
  is allowed, because I am the only member.
- Scoring is hybrid: vector similarity plus a keyword bonus, a small
  penalty for workbook summary rows, and an intent bonus that favours
  the primary record type a question asks about (a bug question
  favours bug reports, an API question favours API cases). A fixed set
  of 12 questions measures this. Pure vector scoring got Hit@1 6/12
  (50%) and Hit@5 10/12 (83%). After the hybrid fix the same set gets
  Hit@1 7/12 (58%) and Hit@5 11/12 (92%). The misses that remain are
  written down in reports/retrieval_eval.md, not hidden.
- Answers come from a small FastAPI service (POST /ask, GET /health)
  or from the command line. A citation validator checks that every
  source an answer names really is in the retrieved set. An answer
  that cites a made-up source is rejected.
- Bring your own key: the app ships with no API key and no default
  paid model. The default answering mode is extractive, which uses no
  language model at all and composes the answer from the retrieved
  document fields, with citations. If I want a real model to write the
  answers, I plug in my own provider, key and model (OpenAI-compatible
  endpoints, Gemini, Anthropic, or a local Ollama) through the
  settings endpoint or the command line flags. The strict prompt and
  the citation check stay the same whichever model answers.
- Eleven pytest tests pass: the three from Tahap 1 plus tests for the
  citation validator, for the OpenAI-compatible request shape (with
  the HTTP call mocked, no real key and no real call), for the
  settings endpoint never exposing a stored key, and a retriever
  smoke test.

## Tahap 1, foundation and ingestion

Done and verified by running it:

- Folder structure, design document and ingestion script are in place.
- Copies of both QA workbooks and the Markdown docs live in data/,
  split per project. The original projects were not modified.
- src/ingest.py reads each workbook sheet by sheet. The header row is
  detected from the ID column header instead of being assumed, data
  rows become one chunk each, and fully empty rows are skipped. My
  template has many pre-formatted empty rows, so the script never
  trusts the sheet's max row as a data count. Markdown files are split
  by heading, one section per chunk.
- Real result from the first run: 321 chunks in total, 203 from
  ParaBank and 118 from Chaligula, with 937 empty rows skipped. The
  counts match the workbooks: ParaBank has 33 UI test cases, 8 API
  cases, 6 SQL cases and 8 bugs; Chaligula has 13 manual test cases,
  29 API cases and 2 bugs. The rest of the chunks are requirements,
  scenarios, RTM rows, execution logs, exploratory sessions, summary
  rows and the Markdown documents. Full numbers are in
  reports/ingest_report.md.
- Two sheets named Instructions (one per workbook) were skipped on
  purpose: they hold workbook guidance text, not data rows, and have no
  ID header. The report records this.
- Three pytest tests pass: empty rows are skipped, the known BUG-001
  chunks from both projects exist with the right document IDs and
  content, and running ingestion twice produces an identical
  chunks.jsonl file.

## How to run it

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/ingest.py        # Tahap 1: build the chunks
.venv/bin/python src/embed_index.py   # Tahap 2: build the search index
```

Ask a question from the command line:

```
.venv/bin/python -m src.ask "What happens when a customer orders far above stock?" --project chaligula
```

Or run the API and ask it over HTTP:

```
.venv/bin/uvicorn app:app --app-dir src --port 8000
curl localhost:8000/health
curl -X POST localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "What bug happens with an invalid password?", "project": "parabank"}'
```

With the API running, the chat page is at http://localhost:8000/ in a
browser. Type a question, pick a project, and the answer appears with
its sources. The settings panel at the bottom of the page is where a
user saves their own model provider and key.

Run the evaluations and the tests with:

```
.venv/bin/python eval/run_retrieval_eval.py
.venv/bin/python eval/run_eval.py
.venv/bin/python -m pytest tests/
```

## Using your own model (optional)

The app ships with no key. To let a real model write the answers, set
your own provider, key and model, either in a .env file (see
.env.example), with the settings endpoint, or per question:

```
curl -X POST localhost:8000/settings/llm -H "Content-Type: application/json" -d '{"provider": "openai-compatible", "api_key": "your-own-key", "model": "your-chosen-model", "base_url": "https://api.groq.com/openai/v1"}'
.venv/bin/python -m src.ask "question" --provider gemini --model gemini-2.0-flash
```

GET /settings/llm shows the provider, base URL, model and whether a
key is set. It never returns the key value. The settings file lives at
config/llm_settings.json on your own machine and is gitignored.

## What is next

Tahap 4 is login and roles, then deployment. The known limit that
remains is the one written above: the refusal rule is calibrated on
25 questions, and two of them pass their rescue limits by a small
margin. A bigger golden set is the honest way to harden it. The full
design and stage list are in docs/DESIGN.md.
