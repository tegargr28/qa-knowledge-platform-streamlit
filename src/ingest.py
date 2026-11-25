"""Ingestion for the QA Knowledge Platform (Tahap 1).

Reads the copied QA workbooks and Markdown docs under data/, turns each
workbook row and each Markdown heading section into one chunk, and writes
output/chunks.jsonl plus reports/ingest_report.md.

Rules that matter for Tegar's workbook template:
- The header row is detected, not assumed: the first row in rows 1..6 that
  contains an ID-like header cell. If none is found, row 4 is used as a
  fallback when it looks like a header (at least 3 short labels).
- Fully empty rows are skipped. The template carries many pre-formatted
  empty rows, so nothing here relies on worksheet.max_row as a data count.
- The run is idempotent: output files are rewritten from scratch and chunk
  ids are deterministic, so running twice gives the same result.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
COMPANY = "personal-tegar"
PROJECTS = {
    "parabank": ROOT / "data" / "parabank",
    "chaligula": ROOT / "data" / "chaligula",
}
OUTPUT_FILE = ROOT / "output" / "chunks.jsonl"
REPORT_FILE = ROOT / "reports" / "ingest_report.md"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:60] or "section"


def guess_doc_type(sheet_name):
    name = sheet_name.lower()
    if "bug" in name:
        return "bug_report"
    if "api" in name:
        return "api_test_case"
    if "sql" in name or "database" in name:
        return "sql_test_case"
    if "test cases" in name:
        return "test_case"
    if "scenario" in name:
        return "scenario"
    if "requirement" in name:
        return "requirement"
    if "rtm" in name or "traceability" in name:
        return "rtm"
    if "execution" in name:
        return "execution"
    if "exploratory" in name:
        return "exploratory"
    return "other"


def is_id_header(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    return text == "id" or text.endswith(" id") or text.endswith("_id") or " id" == text[-3:]


def detect_header(ws):
    """Return (header_row_number, headers) or (None, []) if no header found."""
    for row in range(1, 7):
        values = [ws.cell(row=row, column=c).value for c in range(1, ws.max_column + 1)]
        if any(is_id_header(v) for v in values):
            return row, values
    # Fallback: row 4, the template default, if it looks like a header row.
    values = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
    labels = [str(v).strip() for v in values if v not in (None, "")]
    if len(labels) >= 3 and sum(len(x) for x in labels) / len(labels) < 40:
        return 4, values
    return None, []


def find_id_column(headers):
    for idx, value in enumerate(headers):
        if is_id_header(value):
            return idx
    return 0


def cell_text(value):
    if value is None:
        return ""
    return str(value).strip()


def ingest_workbook(project, path, stats):
    chunks = []
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:  # recorded in the report, not hidden
        stats["failed"].append(f"{project}/{path.name}: could not open workbook ({exc})")
        return chunks

    for ws in wb.worksheets:
        sheet_stats = {"chunks": 0, "skipped_empty": 0}
        stats["sheets"][(project, ws.title)] = sheet_stats
        header_row, headers = detect_header(ws)
        if header_row is None:
            stats["failed"].append(
                f"{project}/{path.name} sheet '{ws.title}': no header row detected in rows 1-6 "
                "and row 4 does not look like a header, sheet skipped"
            )
            continue
        headers = [cell_text(h) or f"Column {i + 1}" for i, h in enumerate(headers)]
        id_col = find_id_column(headers)
        doc_type = guess_doc_type(ws.title)

        for row in range(header_row + 1, ws.max_row + 1):
            values = [ws.cell(row=row, column=c).value for c in range(1, len(headers) + 1)]
            texts = [cell_text(v) for v in values]
            if all(t == "" for t in texts):
                sheet_stats["skipped_empty"] += 1
                continue
            doc_id = texts[id_col] if texts[id_col] else f"{slugify(ws.title).upper()}-ROW{row:04d}"
            text = " | ".join(
                f"{headers[i]}: {texts[i]}" for i in range(len(headers)) if texts[i]
            )
            chunk_id = f"{project}:{path.name}:{slugify(ws.title)}:{doc_id}:{row}"
            chunks.append(
                {
                    "id": chunk_id,
                    "text": text,
                    "metadata": {
                        "company": COMPANY,
                        "project": project,
                        "source_file": path.name,
                        "sheet": ws.title,
                        "row_number": row,
                        "doc_id": doc_id,
                        "doc_type": doc_type,
                    },
                }
            )
            sheet_stats["chunks"] += 1
    return chunks


def ingest_markdown(project, path, stats):
    chunks = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    sections = []
    heading, buffer = "top", []
    for line in raw.splitlines():
        match = re.match(r"^#{1,2}\s+(.*)", line)
        if match:
            if buffer:
                sections.append((heading, buffer))
            heading, buffer = match.group(1).strip(), []
        else:
            buffer.append(line)
    if buffer:
        sections.append((heading, buffer))

    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        doc_id = f"{path.stem}-{slugify(heading)}"
        chunks.append(
            {
                "id": f"{project}:{path.name}:{doc_id}",
                "text": f"# {heading}\n{body}" if heading != "top" else body,
                "metadata": {
                    "company": COMPANY,
                    "project": project,
                    "source_file": path.name,
                    "sheet": None,
                    "row_number": None,
                    "doc_id": doc_id,
                    "doc_type": "document",
                    "heading": heading,
                },
            }
        )
        stats["sheets"][(project, path.name)]["chunks"] += 1
    return chunks


def main():
    stats = {"sheets": defaultdict(lambda: {"chunks": 0, "skipped_empty": 0}), "failed": []}
    all_chunks = []

    for project, folder in PROJECTS.items():
        for path in sorted(folder.glob("*.xlsx")):
            all_chunks.extend(ingest_workbook(project, path, stats))
        for path in sorted(folder.glob("*.md")):
            all_chunks.extend(ingest_markdown(project, path, stats))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as fh:
        for chunk in all_chunks:
            fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    per_project = Counter(c["metadata"]["project"] for c in all_chunks)
    per_type = Counter(c["metadata"]["doc_type"] for c in all_chunks)
    total_skipped = sum(s["skipped_empty"] for s in stats["sheets"].values())

    lines = [
        "# Ingest Report",
        "",
        "Generated by src/ingest.py from the files in data/. All counts below come from that run.",
        "",
        f"Total chunks: {len(all_chunks)}",
        f"Empty rows skipped: {total_skipped}",
        "",
        "## Chunks per project",
        "",
    ]
    for project in sorted(per_project):
        lines.append(f"- {project}: {per_project[project]}")
    lines += ["", "## Chunks per sheet / file", "", "| Project | Sheet / File | Chunks | Empty rows skipped |", "|---|---|---|---|"]
    for (project, name) in sorted(stats["sheets"]):
        s = stats["sheets"][(project, name)]
        lines.append(f"| {project} | {name} | {s['chunks']} | {s['skipped_empty']} |")
    lines += ["", "## Chunks per doc type", ""]
    for doc_type in sorted(per_type):
        lines.append(f"- {doc_type}: {per_type[doc_type]}")
    lines += ["", "## Problems", ""]
    if stats["failed"]:
        for item in stats["failed"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.append("")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"Total chunks: {len(all_chunks)}")
    for project in sorted(per_project):
        print(f"  {project}: {per_project[project]}")
    print(f"Empty rows skipped: {total_skipped}")
    print("Per doc type:", dict(sorted(per_type.items())))
    for item in stats["failed"]:
        print("PROBLEM:", item)
    print(f"Wrote {OUTPUT_FILE} and {REPORT_FILE}")


if __name__ == "__main__":
    main()
