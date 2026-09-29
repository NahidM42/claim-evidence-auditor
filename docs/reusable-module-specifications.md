# Reusable Module Prompt Specifications

These specifications describe modules that are implemented and exercised by the project test suite. They are local project copies because `/home/nahidm/projects/reusable-software-modules` was not present when this project was inspected.

## 1. CSV Record Loader

- **Module name:** CSV Record Loader
- **Purpose / problem solved:** Load analyst-maintained CSV tables into typed claim, source, evidence, and verdict records while surfacing malformed files clearly.
- **Inputs and types:** UTF-8 or UTF-8-with-BOM file path (`str | pathlib.Path`); CSV with the schema-specific required header.
- **Outputs and types:** `list[Claim]`, `list[Source]`, `list[Evidence]`, or `list[Verdict]`.
- **Dependencies:** Python standard library `csv`, `pathlib`; local dataclasses.
- **Database dependencies:** None.
- **Environment variables:** None.
- **Security assumptions:** Treat input as data only; do not execute formulas, follow URLs, or fetch remote resources.
- **Validation rules:** Required header names must exist; extra columns are ignored; values are stripped; missing cells become empty strings; rows with excess values and unreadable files raise `ValueError`.
- **Core logic / operations:** Open using `utf-8-sig`; read rows with `DictReader`; validate headers; normalize fields; instantiate matching immutable dataclasses.
- **Error handling / edge cases:** Missing or empty file, no header, missing column, short row, and excess row values. Short rows normalize missing cells to empty strings for audit-level validation.
- **Data flow:** Each loader returns records to the auditor; no records are persisted.
- **API contract:** `load_claims(path)`, `load_sources(path)`, `load_evidence(path)`, `load_verdicts(path)`.
- **Relevant files:** `src/claim_evidence_auditor/loaders.py`, `models.py`.
- **Tests:** CSV loading, missing header columns, CLI operational input error.
- **Acceptance criteria:** Deterministic typed records; clear structural failures; no external dependency or side effect.
- **Known limitations:** CSV only; errors identify file/line for structural faults but not each record's original line in subsequent validation.
- **Integration points:** CLI loads all four datasets before auditing.
- **Expected UI behavior:** None; CLI reports input/output errors on stderr and returns 2.
- **Expected backend behavior:** Pure local file reads and value normalization.
- **Example input/output:** `claim_id,claim_text,topic,claimant,claim_date,notes` followed by `C1,Example,demo,Analyst,2025-01-01,` becomes `Claim("C1", "Example", "demo", "Analyst", "2025-01-01", "")`.
- **Complete reusable prompt:** “Implement a small standard-library CSV loader for typed claim, source, evidence, and verdict records. Require documented headers, normalize BOM/whitespace/empty cells, return dataclass lists, and raise readable file/schema errors. Do not perform semantic truth checks or network access. Add tests for valid loading, missing headers, empty files, and malformed rows.”

## 2. Deterministic Audit Validator

- **Module name:** Claim–Evidence Validator
- **Purpose / problem solved:** Identify incomplete, duplicate, invalid, or disconnected records consistently without silently changing analyst input.
- **Inputs and types:** Lists of `Claim`, `Source`, `Evidence`, and `Verdict` dataclasses.
- **Outputs and types:** `(list[AuditIssue], list[AuditIssue])`, partitioned into errors and warnings.
- **Dependencies:** Python standard library `collections.Counter`, `datetime.date`; local models.
- **Database dependencies:** None.
- **Environment variables:** None.
- **Security assumptions:** Inputs are untrusted plain values; never dereference URL fields.
- **Validation rules:** Unique non-empty claim/source/evidence IDs; required claim text and source metadata; valid ISO dates; valid stance and verdict taxonomy; evidence and verdict references must exist; verdict rationale required; at most one verdict per claim. Claims without evidence and verdicts without evidence are warnings.
- **Core logic / operations:** Count identifiers, build known-ID sets, validate each table and cross-table relationship, return issues with stable codes and messages.
- **Error handling / edge cases:** Empty identifiers, duplicate IDs, bad dates (including noncanonical ISO spellings), unknown references, invalid enum values, no evidence, duplicate verdict.
- **Data flow:** Audit receives error/warning collections and continues to produce a reviewable report.
- **API contract:** `validate_records(claims, sources, evidence, verdicts) -> tuple[list[AuditIssue], list[AuditIssue]]`.
- **Relevant files:** `src/claim_evidence_auditor/validators.py`, `models.py`.
- **Tests:** Duplicate identifiers, missing fields, unknown relationships, invalid stance/verdict, missing rationale, strict dates, and completeness warnings.
- **Acceptance criteria:** Deterministic issue ordering and stable codes; no automatic correction or trust score.
- **Known limitations:** Duplicate identifiers can make later claim-level summaries ambiguous; validation marks the dataset invalid but does not resolve ambiguity.
- **Integration points:** Called by `auditor.audit`; CLI maps any errors to exit 1.
- **Expected UI behavior:** Human-readable issue lines identify severity, code, and record ID when available.
- **Expected backend behavior:** Validation is local and side-effect free.
- **Example input/output:** Evidence referring to unknown `C-404` returns error code `unknown_claim_reference`; a known claim with no evidence receives warning code `claim_without_evidence`.
- **Complete reusable prompt:** “Build a deterministic validator for claim/source/evidence/verdict records. Check required values, duplicate IDs, references, strict ISO dates, stance and verdict enums, verdict rationale, duplicate verdicts, and evidence completeness. Separate errors from warnings, use stable codes, do not mutate records, and never infer truth or source trust. Cover each rule with focused tests.”

## 3. Evidence Summary and Report Renderer

- **Module name:** Claim Evidence Summary and Reports
- **Purpose / problem solved:** Turn validated records into consistent per-claim evidence summaries and reviewable JSON/Markdown artifacts.
- **Inputs and types:** Record lists and optional `datetime` run time; output directory path.
- **Outputs and types:** `AuditResult`, JSON text, Markdown text, and paths to generated report files.
- **Dependencies:** Python standard library `dataclasses`, `datetime`, `json`, `pathlib`; local models and validator.
- **Database dependencies:** None.
- **Environment variables:** None.
- **Security assumptions:** Report contents are data supplied by local CSVs; Markdown pipes/newlines are escaped for readable tables. URLs are displayed, not fetched.
- **Validation rules:** Carries validation errors and warnings into result; only known sources are listed; verdicts are copied explicitly.
- **Core logic / operations:** Group evidence by claim; count stance labels; count unique mapped source IDs; attach verdict/rationale; serialize dataclass result to JSON; render claim sections and issues to Markdown; create output directory and write two files.
- **Error handling / edge cases:** Claims with zero evidence and verdicts missing from the input still receive summaries; invalid references remain visible as issues and are omitted from valid source lists.
- **Data flow:** `audit()` returns a shared result object consumed by both renderers, preventing separate calculation paths.
- **API contract:** `audit(...) -> AuditResult`, `render_json(result) -> str`, `render_markdown(result) -> str`, `write_reports(result, output_dir) -> tuple[Path, Path]`.
- **Relevant files:** `src/claim_evidence_auditor/auditor.py`, `reports.py`, `models.py`.
- **Tests:** Evidence counts and unique sources, explicit verdict preservation, deterministic supplied run time, JSON parse, Markdown contents, written artifacts.
- **Acceptance criteria:** Both reports reflect the same audit result; no score or auto-verdict; output is reproducible when run time is supplied.
- **Known limitations:** Reports are optimized for small datasets; JSON embeds all summaries; Markdown does not print each evidence excerpt inline.
- **Integration points:** CLI writes reports and chooses process status from `AuditResult.is_valid`.
- **Expected UI behavior:** Markdown clearly shows validation status, claim text, evidence counts, sources, analyst verdict, and rationale.
- **Expected backend behavior:** No network, database, or nondeterministic truth inference.
- **Example input/output:** One `supports` evidence record from source `S1` yields count `supports: 1`, `unique_sources: 1`, and the explicitly entered verdict (or `null` when absent).
- **Complete reusable prompt:** “Implement a standard-library audit summarizer and JSON/Markdown report renderer for linked claim, source, evidence, and analyst verdict records. Include validation issues, evidence stance counts, unique sources, source references, verdict rationale, and run metadata. Never calculate truth from counts. Keep rendering from one shared result model and test the content and file outputs.”

## 4. Audit CLI

- **Module name:** Claim–Evidence Audit CLI
- **Purpose / problem solved:** Make the complete local review workflow easy to run and automate.
- **Inputs and types:** `argparse` command `audit`; four required CSV paths and output directory.
- **Outputs and types:** Console status and two report files; integer process status 0, 1, or 2.
- **Dependencies:** Python standard library `argparse`, `sys`; package loaders, auditor, and report writer.
- **Database dependencies:** None.
- **Environment variables:** None.
- **Security assumptions:** Runs only on the supplied local paths; paths are user-selected; does not contact external services.
- **Validation rules:** Required CLI flags are enforced by argparse; semantic findings are handled by validator.
- **Core logic / operations:** Parse flags; load all datasets; audit; write reports; print issue details and paths; return status based on validation or operational failure.
- **Error handling / edge cases:** Bad arguments use argparse's conventional exit 2; file/report input-output failures return 2; validation errors return 1; clean audit returns 0.
- **Data flow:** User paths → loaders → audit result → reports and exit status.
- **API contract:** `build_parser() -> ArgumentParser`; `main(argv=None) -> int`; console entry point `claim-evidence-auditor`.
- **Relevant files:** `src/claim_evidence_auditor/cli.py`, `pyproject.toml`.
- **Tests:** Valid command, invalid-data command, missing-file return code, output report generation.
- **Acceptance criteria:** Simple help and predictable machine-usable exit codes.
- **Known limitations:** No command for JSON input or individual report formats.
- **Integration points:** Exposed through the project script entry point.
- **Expected UI behavior:** Brief completion line, report paths, and individual issue lines on stderr.
- **Expected backend behavior:** Synchronous local execution.
- **Example input/output:** A clean audit prints “Audit passed: 0 error(s), 0 warning(s).” and exits 0.
- **Complete reusable prompt:** “Create a small argparse CLI that accepts four CSV paths and an output directory, calls an existing audit workflow, writes JSON and Markdown reports, prints validation details, and uses distinct exit codes for valid data, validation errors, and input/output failures. Test success and failure behavior.”
