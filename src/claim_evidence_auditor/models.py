"""Typed records used by the claim-evidence audit workflow."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    claim_text: str
    topic: str = ""
    claimant: str = ""
    claim_date: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    title: str
    publisher: str = ""
    url: str = ""
    publication_date: str = ""
    source_type: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    claim_id: str
    source_id: str
    evidence_text: str
    stance: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class Verdict:
    claim_id: str
    verdict: str
    rationale: str


@dataclass(frozen=True, slots=True)
class AuditIssue:
    severity: str
    code: str
    message: str
    record_id: str = ""


@dataclass(frozen=True, slots=True)
class ClaimSummary:
    claim_id: str
    claim_text: str
    topic: str
    claimant: str
    claim_date: str
    evidence_total: int
    supports: int
    refutes: int
    context: int
    unclear: int
    unique_sources: int
    sources: tuple[dict[str, str], ...]
    verdict: str | None
    rationale: str | None


@dataclass(frozen=True, slots=True)
class AuditResult:
    run_metadata: dict[str, str]
    dataset_summary: dict[str, int]
    errors: tuple[AuditIssue, ...]
    warnings: tuple[AuditIssue, ...]
    claim_summaries: tuple[ClaimSummary, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def record_dict(record: Any) -> dict[str, Any]:
    """Convert a dataclass record to a plain JSON-ready mapping."""
    return asdict(record)

