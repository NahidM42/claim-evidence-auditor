"""Build audit summaries without inferring verdicts from evidence counts."""

from datetime import UTC, datetime

from .models import AuditResult, Claim, ClaimSummary, Evidence, Source, Verdict
from .validators import validate_records


def audit(claims: list[Claim], sources: list[Source], evidence: list[Evidence], verdicts: list[Verdict], *, run_time: datetime | None = None) -> AuditResult:
    errors, warnings = validate_records(claims, sources, evidence, verdicts)
    source_by_id = {source.source_id: source for source in sources}
    evidence_by_claim: dict[str, list[Evidence]] = {}
    for item in evidence:
        evidence_by_claim.setdefault(item.claim_id, []).append(item)
    verdict_by_claim: dict[str, Verdict] = {}
    for item in verdicts:
        verdict_by_claim.setdefault(item.claim_id, item)

    summaries: list[ClaimSummary] = []
    for claim in claims:
        mapped = evidence_by_claim.get(claim.claim_id, [])
        counts = {stance: sum(item.stance == stance for item in mapped) for stance in ("supports", "refutes", "context", "unclear")}
        source_refs = []
        for source_id in sorted({item.source_id for item in mapped if item.source_id in source_by_id}):
            src = source_by_id[source_id]
            source_refs.append({"source_id": src.source_id, "title": src.title, "publisher": src.publisher, "url": src.url})
        verdict = verdict_by_claim.get(claim.claim_id)
        summaries.append(ClaimSummary(
            claim_id=claim.claim_id, claim_text=claim.claim_text, topic=claim.topic, claimant=claim.claimant,
            claim_date=claim.claim_date, evidence_total=len(mapped), supports=counts["supports"],
            refutes=counts["refutes"], context=counts["context"], unclear=counts["unclear"],
            unique_sources=len(source_refs), sources=tuple(source_refs),
            verdict=verdict.verdict if verdict else None, rationale=verdict.rationale if verdict else None,
        ))
    current = run_time or datetime.now(UTC)
    return AuditResult(
        run_metadata={"generated_at": current.isoformat(), "tool": "claim-evidence-auditor", "version": "0.1.0"},
        dataset_summary={"claims": len(claims), "sources": len(sources), "evidence": len(evidence), "verdicts": len(verdicts)},
        errors=tuple(errors), warnings=tuple(warnings), claim_summaries=tuple(summaries),
    )

