# Claim–Evidence Auditor

A small, reproducible Python workflow for organizing claims, sources, mapped evidence, and explicit analyst verdicts. It validates the record and produces machine-readable and human-readable audit reports; it does not decide what is true.

## Problem and approach

Fact-checking records are easier to review when claims, source metadata, evidence excerpts, stance labels, and the analyst's reasoning are connected and validated consistently. This package provides that structure using four CSV files and a deterministic audit pass.

It intentionally does **not** independently determine whether arbitrary real-world claims are true, rank source credibility, browse the web, or derive verdicts from evidence counts. Verdicts remain human-entered classifications with a required rationale.

## Features

- CSV loading for claims, sources, evidence, and verdicts
- Required-field, ID uniqueness, reference, date, stance, and verdict checks
- Error and warning reporting with stable issue codes
- Per-claim stance counts and unique-source counts
- JSON and Markdown reports generated from the same audit result
- CLI exit codes: `0` valid audit, `1` completed audit with validation errors, `2` input/output failure
- No runtime dependencies or external services

## Architecture

`loaders` reads and normalizes CSV data into typed records. `validators` checks schema and relationships. `auditor` builds evidence summaries and carries through analyst verdicts without inferring them. `reports` renders JSON and Markdown. `cli` connects the workflow and returns status codes.

## Repository layout

```text
src/claim_evidence_auditor/  package modules
examples/                    neutral fictional CSV inputs and generated reports
examples/invalid/            intentionally invalid validation demonstration
tests/                        pytest workflow coverage
docs/                         architecture and reusable module specifications
```

## Installation

Requires Python 3.12 or newer and `uv`.

```bash
uv sync --extra dev
```

## Quick start

```bash
uv run claim-evidence-auditor audit \
  --claims examples/claims.csv \
  --sources examples/sources.csv \
  --evidence examples/evidence.csv \
  --verdicts examples/verdicts.csv \
  --output-dir examples/output
```

The command writes `audit-report.json` and `evidence-report.md`. The checked-in example outputs are produced by this command. The sample uses fictional Alderford records and makes no claims about real organizations or events.

A completed valid sample run prints `Audit passed: 0 error(s), 0 warning(s).` and exits with code 0. The generated report summarizes 3 claims, 3 sources, 4 evidence records, and 3 analyst verdicts; for claim `C-002`, it records one refuting item, one contextual item, two unique sources, and the explicitly entered `misleading` verdict. For a validation demonstration, replace each input path with the corresponding file in `examples/invalid/`; validation issues are printed and the command exits with code 1.

## Input schemas

All files are UTF-8 CSV with a header. Every listed column is required in the header; optional values may be blank.

| File | Columns |
|---|---|
| Claims | `claim_id`, `claim_text`, `topic`, `claimant`, `claim_date`, `notes` |
| Sources | `source_id`, `title`, `publisher`, `url`, `publication_date`, `source_type`, `notes` |
| Evidence | `evidence_id`, `claim_id`, `source_id`, `evidence_text`, `stance`, `notes` |
| Verdicts | `claim_id`, `verdict`, `rationale` |

Dates, when supplied, must use ISO `YYYY-MM-DD`. Source IDs and metadata fields title, publisher, URL, and source type are required. URLs are stored as analyst-provided references; the program does not fetch them.

### Evidence stances

- `supports`
- `refutes`
- `context`
- `unclear`

### Verdicts

- `supported`
- `false`
- `misleading`
- `insufficient_evidence`

A verdict requires a rationale. Evidence count summaries are descriptive and never produce a truth score or verdict.

## Example report

The generated Markdown report groups records by claim and shows mapped sources, evidence counts, verdict rationale, and validation status. The JSON report contains run metadata, dataset counts, errors, warnings, and claim-level summaries. Reports preserve the analyst verdict exactly as entered.

## Testing and quality checks

```bash
uv run pytest
uv run ruff check .
```

## Design decisions

- Uses Python standard-library CSV, dataclasses, JSON, dates, and argparse for a small runtime footprint.
- Accepts records with duplicate or missing IDs where possible so the auditor can report record-level problems instead of stopping at the first bad row.
- Treats malformed CSV headers/rows and unreadable files as operational input errors (exit 2); schema and relationship problems are collected in reports (exit 1).
- Uses stable issue codes to support review and downstream processing.

## Limitations

Input is CSV only. Date validation checks ISO calendar dates but not chronology. URL syntax and source credibility are not assessed. The tool does not retrieve sources, verify quotations, reconcile conflicting evidence, or assign verdicts. Duplicate IDs make some summary associations inherently ambiguous; validation marks those records invalid for review.

## Possible future improvements

JSON input, richer CSV line references in issues, configurable schema profiles, and report formats designed for larger evidence collections could be added if a concrete user workflow calls for them.

## Skills demonstrated

Python packaging and CLI design, structured data modeling, deterministic validation, evidence traceability, report generation, automated testing, and clear limits on machine-assisted judgments.
