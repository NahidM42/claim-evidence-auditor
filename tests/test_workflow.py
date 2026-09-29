import json
from datetime import UTC, datetime

import pytest

from claim_evidence_auditor.auditor import audit
from claim_evidence_auditor.cli import main
from claim_evidence_auditor.loaders import load_claims, load_evidence, load_sources, load_verdicts
from claim_evidence_auditor.models import Claim, Evidence, Source, Verdict
from claim_evidence_auditor.reports import render_json, render_markdown, write_reports
from claim_evidence_auditor.validators import validate_records


@pytest.fixture
def records():
    claims = [Claim("C1", "A fictional statement", "demo", "Analyst", "2025-01-01")]
    sources = [Source("S1", "Record", "Publisher", "https://example.org", "2025-01-02", "archive")]
    evidence = [Evidence("E1", "C1", "S1", "A recorded fact", "supports")]
    verdicts = [Verdict("C1", "supported", "The record explicitly documents the statement.")]
    return claims, sources, evidence, verdicts


def test_sample_csv_loading():
    assert len(load_claims("examples/claims.csv")) == 3
    assert len(load_sources("examples/sources.csv")) == 3
    assert len(load_evidence("examples/evidence.csv")) == 4
    assert len(load_verdicts("examples/verdicts.csv")) == 3


def test_loader_rejects_missing_column(tmp_path):
    path = tmp_path / "claims.csv"
    path.write_text("claim_id,claim_text\nC1,Text\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required column"):
        load_claims(path)


def test_validation_catches_duplicate_ids_unknown_references_and_taxonomies(records):
    claims, sources, evidence, verdicts = records
    claims.append(Claim("C1", "duplicate"))
    evidence += [Evidence("E1", "ABSENT", "ABSENT", "text", "agrees")]
    verdicts.append(Verdict("ABSENT", "probably true", "rationale"))
    errors, _ = validate_records(claims, sources, evidence, verdicts)
    codes = {issue.code for issue in errors}
    assert {"duplicate_claim_id", "duplicate_evidence_id", "unknown_claim_reference", "unknown_source_reference", "invalid_stance", "unknown_verdict_claim", "invalid_verdict"} <= codes


def test_missing_required_values_dates_and_rationale(records):
    _, _, evidence, _ = records
    errors, _ = validate_records([Claim("", "", claim_date="yesterday")], [Source("S2", "")], evidence, [Verdict("C1", "false", "")])
    codes = {issue.code for issue in errors}
    assert {"missing_claim_id", "missing_claim_text", "invalid_date", "missing_source_title", "missing_source_publisher", "missing_source_url", "missing_source_source_type", "missing_verdict_rationale"} <= codes


def test_warnings_for_claim_without_evidence_and_verdict_without_evidence(records):
    claims, sources, _, verdicts = records
    _, warnings = validate_records(claims, sources, [], verdicts)
    assert {issue.code for issue in warnings} == {"claim_without_evidence", "verdict_without_evidence"}


def test_summary_is_explicit_not_an_inferred_truth_score(records):
    claims, sources, evidence, verdicts = records
    evidence.extend([Evidence("E2", "C1", "S1", "counterpoint", "refutes"), Evidence("E3", "C1", "S1", "context", "context")])
    result = audit(claims, sources, evidence, verdicts, run_time=datetime(2025, 1, 1, tzinfo=UTC))
    summary = result.claim_summaries[0]
    assert (summary.evidence_total, summary.supports, summary.refutes, summary.context, summary.unclear) == (3, 1, 1, 1, 0)
    assert summary.unique_sources == 1
    assert summary.verdict == "supported"
    assert result.run_metadata["generated_at"] == "2025-01-01T00:00:00+00:00"


def test_json_and_markdown_reports(records, tmp_path):
    result = audit(*records, run_time=datetime(2025, 1, 1, tzinfo=UTC))
    parsed = json.loads(render_json(result))
    assert parsed["claim_summaries"][0]["verdict"] == "supported"
    markdown = render_markdown(result)
    assert "Claim–Evidence Audit Report" in markdown
    assert "Analyst verdict:** supported" in markdown
    json_path, md_path = write_reports(result, tmp_path / "reports")
    assert json_path.exists() and md_path.exists()


def test_cli_success_and_validation_failure(tmp_path, capsys):
    args = ["audit", "--claims", "examples/claims.csv", "--sources", "examples/sources.csv", "--evidence", "examples/evidence.csv", "--verdicts", "examples/verdicts.csv", "--output-dir", str(tmp_path / "out")]
    assert main(args) == 0
    assert "Audit passed" in capsys.readouterr().out
    args[1:3] = ["--claims", "examples/invalid/claims.csv"]
    args[3:5] = ["--sources", "examples/invalid/sources.csv"]
    args[5:7] = ["--evidence", "examples/invalid/evidence.csv"]
    args[7:9] = ["--verdicts", "examples/invalid/verdicts.csv"]
    assert main(args) == 1
    assert "invalid_stance" in capsys.readouterr().err


def test_cli_input_error_exit_code(tmp_path, capsys):
    code = main(["audit", "--claims", str(tmp_path / "missing.csv"), "--sources", "x", "--evidence", "x", "--verdicts", "x", "--output-dir", "out"])
    assert code == 2
    assert "cannot read" in capsys.readouterr().err



def test_duplicate_source_and_verdict_ids_and_strict_iso_dates(records):
    claims, sources, evidence, verdicts = records
    sources.append(Source("S1", "Duplicate", "Publisher", "https://example.org", "20250102", "archive"))
    verdicts.append(Verdict("C1", "false", "Conflicting analyst conclusion."))
    errors, _ = validate_records(claims, sources, evidence, verdicts)
    codes = {issue.code for issue in errors}
    assert {"duplicate_source_id", "duplicate_verdict", "invalid_date"} <= codes
