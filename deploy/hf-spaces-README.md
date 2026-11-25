---
title: QA Knowledge Platform
emoji: "🔎"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# QA Knowledge Platform

A question and answer system over my own QA documents (ParaBank and
Chaligula QA): Excel workbooks and Markdown docs turned into searchable
chunks, answers composed only from what the search finds, with sources
that are checked before an answer is shown, and a 25-question
evaluation set (25/25, gate 80%) that includes trap questions the
system must refuse.

It runs in personal mode on a free CPU Space. Answers are extractive
by default and need no API key. If you want a real model to write the
answers, bring your own key: open the settings panel in the app and
plug in your own provider, model and key (OpenAI-compatible endpoints,
Gemini, Anthropic, or a local Ollama). No key is bundled with the app
and no key is stored on the server side beyond your own session
settings file.

Full documentation, design and evaluation reports live in the GitHub
repository README (this file is the short Space-facing version, kept
separate so the main README stays a normal portfolio README).
