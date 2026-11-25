# Design: QA Knowledge Platform

## What this is

A question and answer system over QA documents: test cases, bug reports,
scenarios, requirements and test plans. A user asks a question in plain
language, the system first searches the documents, and only then asks an
LLM to answer from what was found. Every answer has to name its source,
and a validator checks that the named source really exists in the
retrieved documents.

## Enterprise design

The data model follows how a large company is organised:

```
Company
  Project (one product or one test effort)
    Sources (Excel workbooks, Markdown docs, later Jira and Confluence)
    Members, each with a role
  Roles: Company Admin, QA Lead, QA Engineer, Auditor (read only)
```

Rules that come from that hierarchy:

- A member only ever searches documents from projects they belong to.
  The permission filter runs before the search, not after it, so data
  from another project cannot leak through an answer.
- Every question and answer is written to an audit log: who asked, what
  they asked, what the system answered, and when.
- Documents are re-ingested when they change. A deleted source document
  removes its chunks as well.

## The three flows

1. Ingestion. Sources are read, split into chunks, and stored with
   metadata: company, project, source file, sheet or heading, row
   number, document ID and document type. For Excel workbooks one row
   becomes one chunk. For Markdown one heading section becomes one chunk.
2. Question and answer. The user asks a question. The system filters by
   the user's project permissions, searches for the most relevant
   chunks, sends only those chunks to the LLM with a strict instruction
   (answer only from these documents, cite the document ID, refuse if
   the answer is not there), then validates the citations before
   showing the answer.
3. Evaluation. A fixed set of test questions with known correct sources
   is run against the system after every change, like regression testing
   for the AI. Scores are reported per project. A change that drops the
   score below the agreed threshold is not shipped.

## Personal mode

This is one application, not two. Personal mode is the same system with
the company size set to one:

- The company is "personal-tegar" and the only member holds every role.
- Login and SSO are off. Sources are local files (Excel and Markdown)
  instead of company connectors. The LLM is a free public provider
  instead of a company one. Audit is a simple question history.
- Nothing in the chunk format or the ingestion code changes between
  modes, so work done in personal mode is not thrown away later.

## Tech stack

- Backend: Python and FastAPI (from Tahap 2 on)
- Relational data (companies, projects, members, audit): PostgreSQL
- Vector search: pgvector or Qdrant (later stage; Tahap 1 stops at a
  chunks.jsonl file so the data can be inspected by hand)
- LLM access: one gateway module that can point at Gemini, Groq, Azure
  OpenAI or a self hosted model, so the rest of the app never changes
  when the provider changes
- Observability: Langfuse or equivalent for cost, latency and errors
  (later stage)
- Deployment for a company: Docker, inside the company's own network

## Build stages

1. Tahap 1 (done): foundation and ingestion. Workbooks and Markdown
   docs from the ParaBank and Chaligula QA projects become chunks.
2. Tahap 2 (done): embeddings, vector search and the question and
   answer API. The citation validator arrived early in this stage;
   the LLM gateway is bring-your-own-key, with an extractive no-key
   default.
3. Tahap 3 (done): refusal behaviour with a calibrated relevance
   threshold, a 25-question golden set that scores the full answer
   pipeline against an 80% gate, and a simple chat page served by the
   API.
4. Tahap 4: login and roles.
5. Tahap 5: deployment, then company connectors (Jira, Confluence).
