"""Capstone Task 6: deterministic loan-application status lookup and escalation."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any

from dataset import LOAN_APPLICATIONS


MOCK_LLM = "MOCK_LLM (no external API calls)"
PERCENTILE = 0.80
FORMULA = "0.70 * fraud_flag + 0.30 * (1 - days_since_created / 30)"


def escalation_score(record: dict[str, Any]) -> float:
    """Calculate the specified transparent escalation score for one dataset record."""
    fraud_flag = 1.0 if record["flagged_for_fraud_review"] else 0.0
    score = 0.70 * fraud_flag + 0.30 * (1 - record["days_since_created"] / 30)
    if not 0 <= score <= 1:
        raise ValueError(f"Escalation score is outside [0, 1]: {score}")
    return score


def score_distribution(records: list[dict[str, Any]]) -> dict[float, int]:
    """Return ascending score frequencies calculated from the supplied records."""
    frequencies = Counter(escalation_score(record) for record in records)
    return dict(sorted(frequencies.items()))


def escalation_threshold(records: list[dict[str, Any]]) -> float:
    """Return the nearest-rank 80th-percentile score from generated applications."""
    if not records:
        raise ValueError("Cannot calculate an escalation threshold from an empty dataset")
    sorted_scores = sorted(escalation_score(record) for record in records)
    percentile_index = math.ceil(PERCENTILE * len(sorted_scores)) - 1
    return sorted_scores[percentile_index]


def check_loan_application_status(record_id: str) -> dict[str, Any]:
    """Look up a generated application and return its required status details."""
    record = next(
        (item for item in LOAN_APPLICATIONS if item["record_id"] == record_id),
        None,
    )
    if record is None:
        raise ValueError(f"Unknown record ID: {record_id}")
    return {
        "record_id": record["record_id"],
        "status": record["status"],
        "loan_amount_inr": record["loan_amount_inr"],
        "escalation_score": escalation_score(record),
    }


def write_report(report_path: Path) -> tuple[float, dict[float, int], int]:
    """Write the Task 6 formula, generated score distribution, and threshold rationale."""
    distribution = score_distribution(LOAN_APPLICATIONS)
    threshold = escalation_threshold(LOAN_APPLICATIONS)
    high_risk_count = sum(
        escalation_score(record) >= threshold for record in LOAN_APPLICATIONS
    )
    distribution_lines = [
        f"- `{score:.4f}`: {count} application(s)"
        for score, count in distribution.items()
    ]
    report = "\n".join(
        [
            "# Cred Capstone Task 6 Report",
            "",
            f"- LLM mode: `{MOCK_LLM}`",
            f"- Generated applications scored: {len(LOAN_APPLICATIONS)}",
            "",
            "## Exact escalation formula",
            "",
            f"`escalation_score = {FORMULA}`",
            "",
            "`fraud_flag` is 1.0 for a fraud-review flag and 0.0 otherwise. A flagged, "
            "newly created application therefore reaches 1.0, while an unflagged application "
            "at 30 days reaches 0.0.",
            "",
            "## Score distribution",
            "",
            *distribution_lines,
            "",
            "## Escalation threshold",
            "",
            f"The nearest-rank 80th-percentile threshold is **{threshold:.4f}**.",
            f"{high_risk_count} of {len(LOAN_APPLICATIONS)} generated applications have scores "
            "at or above this threshold. This selects the highest-risk approximately 20% of "
            "the generated set; equal scores at the boundary can include additional records.",
            "",
        ]
    )
    report_path.write_text(report, encoding="utf-8")
    return threshold, distribution, high_risk_count


def main() -> None:
    """Write the report and demonstrate two lookups plus the required error path."""
    project_dir = Path(__file__).resolve().parent
    threshold, distribution, high_risk_count = write_report(
        project_dir / "task_6_report.md"
    )
    print(f"MOCK_LLM mode: {MOCK_LLM}")
    print(f"Score distribution contains {len(distribution)} distinct score(s).")
    print(
        f"80th-percentile escalation threshold: {threshold:.4f} "
        f"({high_risk_count}/{len(LOAN_APPLICATIONS)} at or above threshold)"
    )
    for record_id in ("LA-001", "LA-002"):
        print(check_loan_application_status(record_id))
    try:
        check_loan_application_status("LA-999")
    except ValueError as error:
        print(f"Unknown-ID demonstration: {error}")


if __name__ == "__main__":
    main()
