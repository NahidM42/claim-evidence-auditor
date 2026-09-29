"""Command line entry point."""

import argparse
import sys

from .auditor import audit
from .loaders import load_claims, load_evidence, load_sources, load_verdicts
from .reports import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claim-evidence-auditor", description="Audit claim, source, evidence, and analyst verdict CSV files.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("audit", help="validate inputs and generate JSON and Markdown reports")
    run.add_argument("--claims", required=True, help="claims CSV path")
    run.add_argument("--sources", required=True, help="sources CSV path")
    run.add_argument("--evidence", required=True, help="evidence CSV path")
    run.add_argument("--verdicts", required=True, help="verdicts CSV path")
    run.add_argument("--output-dir", required=True, help="directory for audit-report.json and evidence-report.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = audit(load_claims(args.claims), load_sources(args.sources), load_evidence(args.evidence), load_verdicts(args.verdicts))
        json_path, markdown_path = write_reports(result, args.output_dir)
    except (ValueError, OSError) as exc:
        print(f"Input/output error: {exc}", file=sys.stderr)
        return 2
    for issue in (*result.errors, *result.warnings):
        print(f"{issue.severity.upper()} [{issue.code}]{f' ({issue.record_id})' if issue.record_id else ''}: {issue.message}", file=sys.stderr)
    print(f"Audit {'passed' if result.is_valid else 'failed'}: {len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    print(f"JSON: {json_path}\nMarkdown: {markdown_path}")
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

