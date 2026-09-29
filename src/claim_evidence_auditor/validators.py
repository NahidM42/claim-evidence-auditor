"""Deterministic schema, relationship, and completeness checks."""

from collections import Counter
from datetime import date

from .models import AuditIssue, Claim, Evidence, Source, Verdict

STANCES = {"supports", "refutes", "context", "unclear"}
VERDICTS = {"supported", "false", "misleading", "insufficient_evidence"}


def _issue(severity: str, code: str, message: str, record_id: str = "") -> AuditIssue:
    return AuditIssue(severity, code, message, record_id)


def _date_issue(value: str, field: str, record_id: str) -> AuditIssue | None:
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        parsed = None
    if parsed is None or parsed.isoformat() != value:
        return _issue("error", "invalid_date", f"{field} must be an ISO date (YYYY-MM-DD); got {value!r}.", record_id)
    return None


def validate_records(claims: list[Claim], sources: list[Source], evidence: list[Evidence], verdicts: list[Verdict]) -> tuple[list[AuditIssue], list[AuditIssue]]:
    errors: list[AuditIssue] = []
    warnings: list[AuditIssue] = []

    for records, id_field, label in ((claims, "claim_id", "claim"), (sources, "source_id", "source"), (evidence, "evidence_id", "evidence")):
        counts = Counter(getattr(row, id_field) for row in records if getattr(row, id_field))
        for identifier, count in sorted(counts.items()):
            if count > 1:
                errors.append(_issue("error", f"duplicate_{label}_id", f"{label.title()} ID {identifier!r} appears {count} times.", identifier))

    claim_ids = {row.claim_id for row in claims if row.claim_id}
    source_ids = {row.source_id for row in sources if row.source_id}
    claims_with_evidence: set[str] = set()
    evidence_counts = Counter(row.claim_id for row in evidence if row.claim_id)

    for row in claims:
        if not row.claim_id:
            errors.append(_issue("error", "missing_claim_id", "Claim ID is required."))
        if not row.claim_text:
            errors.append(_issue("error", "missing_claim_text", "Claim text is required.", row.claim_id))
        problem = _date_issue(row.claim_date, "claim_date", row.claim_id)
        if problem:
            errors.append(problem)
        if row.claim_id and not evidence_counts[row.claim_id]:
            warnings.append(_issue("warning", "claim_without_evidence", "Claim has no mapped evidence.", row.claim_id))

    for row in sources:
        if not row.source_id:
            errors.append(_issue("error", "missing_source_id", "Source ID is required."))
        for field, value in (("title", row.title), ("publisher", row.publisher), ("url", row.url), ("source_type", row.source_type)):
            if not value:
                errors.append(_issue("error", f"missing_source_{field}", f"Source {field} is required.", row.source_id))
        problem = _date_issue(row.publication_date, "publication_date", row.source_id)
        if problem:
            errors.append(problem)

    for row in evidence:
        if not row.evidence_id:
            errors.append(_issue("error", "missing_evidence_id", "Evidence ID is required."))
        if not row.claim_id or row.claim_id not in claim_ids:
            errors.append(_issue("error", "unknown_claim_reference", f"Evidence refers to nonexistent claim {row.claim_id!r}.", row.evidence_id))
        else:
            claims_with_evidence.add(row.claim_id)
        if not row.source_id or row.source_id not in source_ids:
            errors.append(_issue("error", "unknown_source_reference", f"Evidence refers to nonexistent source {row.source_id!r}.", row.evidence_id))
        if not row.evidence_text:
            errors.append(_issue("error", "missing_evidence_text", "Evidence text is required.", row.evidence_id))
        if row.stance not in STANCES:
            errors.append(_issue("error", "invalid_stance", f"Stance must be one of {', '.join(sorted(STANCES))}; got {row.stance!r}.", row.evidence_id))

    seen_verdict_claims: set[str] = set()
    for row in verdicts:
        if not row.claim_id or row.claim_id not in claim_ids:
            errors.append(_issue("error", "unknown_verdict_claim", f"Verdict refers to nonexistent claim {row.claim_id!r}.", row.claim_id))
        if row.claim_id in seen_verdict_claims:
            errors.append(_issue("error", "duplicate_verdict", "Claim has more than one verdict.", row.claim_id))
        seen_verdict_claims.add(row.claim_id)
        if row.verdict not in VERDICTS:
            errors.append(_issue("error", "invalid_verdict", f"Verdict must be one of {', '.join(sorted(VERDICTS))}; got {row.verdict!r}.", row.claim_id))
        if not row.rationale:
            errors.append(_issue("error", "missing_verdict_rationale", "A verdict rationale is required.", row.claim_id))
        if row.claim_id in claim_ids and row.claim_id not in claims_with_evidence:
            warnings.append(_issue("warning", "verdict_without_evidence", "Verdict has no mapped evidence.", row.claim_id))

    return errors, warnings

