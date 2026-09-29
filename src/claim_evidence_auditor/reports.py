"""JSON and Markdown renderers for audit results."""

import json
from dataclasses import asdict
from pathlib import Path

from .models import AuditResult


def render_json(result: AuditResult) -> str:
    return json.dumps(asdict(result), indent=2, ensure_ascii=False) + "\n"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(result: AuditResult) -> str:
    lines = ["# Claim–Evidence Audit Report", "", f"Generated: {result.run_metadata['generated_at']}", "",
             "## Dataset", "", " | ".join(f"{key.title()}: {value}" for key, value in result.dataset_summary.items()), "",
             "## Validation", "", f"**Status:** {'PASS' if result.is_valid else 'FAIL'} — {len(result.errors)} error(s), {len(result.warnings)} warning(s).", ""]
    for title, issues in (("Errors", result.errors), ("Warnings", result.warnings)):
        if issues:
            lines.extend([f"### {title}", ""])
            lines.extend(f"- `{issue.code}`{f' ({issue.record_id})' if issue.record_id else ''}: {issue.message}" for issue in issues)
            lines.append("")
    lines.extend(["## Claim reviews", ""])
    for claim in result.claim_summaries:
        lines.extend([f"### {claim.claim_id}: {_escape(claim.claim_text)}", ""])
        if claim.topic or claim.claimant or claim.claim_date:
            lines.append(" · ".join(value for value in (claim.topic, claim.claimant, claim.claim_date) if value))
            lines.append("")
        lines.extend(["| Evidence total | Supports | Refutes | Context | Unclear | Unique sources |", "|---:|---:|---:|---:|---:|---:|",
                      f"| {claim.evidence_total} | {claim.supports} | {claim.refutes} | {claim.context} | {claim.unclear} | {claim.unique_sources} |", ""])
        if claim.sources:
            lines.append("**Sources**")
            lines.append("")
            lines.extend(f"- `{_escape(src['source_id'])}` — {_escape(src['title'])}, {_escape(src['publisher'])} ({_escape(src['url'])})" for src in claim.sources)
            lines.append("")
        else:
            lines.extend(["**Sources:** None mapped", ""])
        lines.append(f"**Analyst verdict:** {claim.verdict or 'Not provided'}")
        if claim.rationale:
            lines.append(f"**Rationale:** {_escape(claim.rationale)}")
        lines.append("")
    lines.extend(["---", "", "Evidence counts describe the mapped records; they do not determine whether a claim is true. Verdicts are explicit analyst judgments.", ""])
    return "\n".join(lines)


def write_reports(result: AuditResult, output_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "audit-report.json"
    markdown_path = directory / "evidence-report.md"
    json_path.write_text(render_json(result), encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, markdown_path

