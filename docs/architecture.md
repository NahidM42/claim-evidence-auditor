# Architecture

The package follows a small, one-way pipeline:

```text
CSV files -> loaders -> typed records -> validators -> audit summaries -> JSON / Markdown
                                                    ^
                                             analyst verdicts
```

- `models.py` defines immutable dataclasses for input records, audit issues, summaries, and results.
- `loaders.py` normalizes UTF-8 CSV values and reports structural/file errors.
- `validators.py` checks required values, identifiers, relationships, enumerations, dates, and missing evidence.
- `auditor.py` aggregates evidence stance counts and source references while preserving entered verdicts.
- `reports.py` renders the same result as JSON and Markdown.
- `cli.py` binds input loading, auditing, report writing, messages, and exit codes.

The validator reports problems rather than repairing input. Evidence counts are descriptive only. A verdict can be present even where the input has other errors; the report preserves it while making those errors visible for human review.
