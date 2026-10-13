"""Report evidence-grounding checks and failures in saved classifications."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import ROOT


def summarize(path: Path) -> dict[str, int]:
    records = json.loads(path.read_text(encoding="utf-8"))
    failed = [record for record in records if "classification_error" in record]
    grounded = 0
    missing_evidence = 0
    unsupported = 0
    for record in records:
        if "classification_error" in record:
            continue
        evidence = record.get("supporting_evidence", "")
        comment = record.get("customer_comment", "")
        if evidence and evidence.casefold() in comment.casefold():
            grounded += 1
        elif evidence:
            unsupported += 1
        else:
            missing_evidence += 1
    return {"records": len(records), "classification_errors": len(failed), "evidence_grounded": grounded, "evidence_missing": missing_evidence, "evidence_not_found": unsupported}


if __name__ == "__main__":
    source = ROOT / "data" / "processed" / "classifications.json"
    print(json.dumps(summarize(source), indent=2))
