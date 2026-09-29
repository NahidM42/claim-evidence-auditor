"""CSV input loading with predictable header and decoding errors."""

import csv
from pathlib import Path

from .models import Claim, Evidence, Source, Verdict


def _load_csv[T](path: str | Path, fields: tuple[str, ...], factory: type[T]) -> list[T]:
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"{path}: CSV file is empty or has no header")
            missing = [field for field in fields if field not in reader.fieldnames]
            if missing:
                raise ValueError(f"{path}: missing required column(s): {', '.join(missing)}")
            records: list[T] = []
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"{path}:{line_number}: row has more values than the header")
                values = {field: (row.get(field) or "").strip() for field in fields}
                records.append(factory(**values))
            return records
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def load_claims(path: str | Path) -> list[Claim]:
    return _load_csv(path, ("claim_id", "claim_text", "topic", "claimant", "claim_date", "notes"), Claim)


def load_sources(path: str | Path) -> list[Source]:
    return _load_csv(path, ("source_id", "title", "publisher", "url", "publication_date", "source_type", "notes"), Source)


def load_evidence(path: str | Path) -> list[Evidence]:
    return _load_csv(path, ("evidence_id", "claim_id", "source_id", "evidence_text", "stance", "notes"), Evidence)


def load_verdicts(path: str | Path) -> list[Verdict]:
    return _load_csv(path, ("claim_id", "verdict", "rationale"), Verdict)

