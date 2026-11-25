"""Citation validator for the QA Knowledge Platform.

An answer is only trustworthy if the sources it names really were in
the retrieved set. This module extracts the citations from an answer
and checks them.

Citation format used across the project: [project:doc_id], for example
[chaligula:BUG-001] or [parabank:README-bugs-i-found]. A bare [doc_id]
is also accepted, but doc IDs repeat between projects (both projects
have a BUG-001), so the project-qualified form is the safe one.
"""

import re

_CITATION_RE = re.compile(r"\[([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)\]")


def extract_citations(answer):
    """Return the raw citation strings found in the answer, in order."""
    found = []
    for match in _CITATION_RE.findall(answer or ""):
        # Skip things that look like markdown link text fragments.
        if match not in found:
            found.append(match)
    return found


def _parse(citation):
    if ":" in citation:
        project, doc_id = citation.split(":", 1)
        return project.strip().lower(), doc_id.strip()
    return None, citation.strip()


def validate_citations(answer, retrieved_chunks):
    """Check every citation in answer against the retrieved chunks.

    retrieved_chunks: list of chunk dicts (with metadata) or retriever
    result dicts (with a "chunk" key).

    Returns {valid, citations, invalid, checked_against}:
    - valid is True only when there is at least one citation and every
      citation exists in the retrieved set.
    - invalid lists the citations that were not found.
    """
    retrieved = []
    for item in retrieved_chunks or []:
        chunk = item.get("chunk", item) if isinstance(item, dict) else item
        meta = chunk.get("metadata", {})
        retrieved.append((meta.get("project", ""), meta.get("doc_id", "")))

    citations = extract_citations(answer)
    invalid = []
    for citation in citations:
        project, doc_id = _parse(citation)
        ok = any(
            doc == doc_id and (project is None or proj == project)
            for proj, doc in retrieved
        )
        if not ok:
            invalid.append(citation)
    return {
        "valid": bool(citations) and not invalid,
        "citations": citations,
        "invalid": invalid,
        "checked_against": sorted({doc for _, doc in retrieved}),
    }
