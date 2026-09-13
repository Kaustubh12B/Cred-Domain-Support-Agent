"""Deterministic loan-application data for Capstone Task 1."""

import random
from collections import Counter
from typing import Any


SEED = 20260912
RECORD_COUNT = 50
MIN_LOAN_AMOUNT_INR = 75_000
MAX_LOAN_AMOUNT_INR = 5_000_000
MAX_DAYS_SINCE_CREATED = 30
FRAUD_PROBABILITY = 0.18

REQUIRED_CATEGORIES = (
    "Personal Loan",
    "Home Loan",
    "Auto Loan",
    "Education Loan",
    "Business Loan",
)
REQUIRED_STATUSES = (
    "Submitted",
    "Under Review",
    "Approved",
    "Rejected",
    "Disbursed",
)
CATEGORY_WEIGHTS = (1 / 5,) * len(REQUIRED_CATEGORIES)
STATUS_WEIGHTS = (1 / 5,) * len(REQUIRED_STATUSES)


def _equal_weight_choice(
    generator: random.Random, options: tuple[str, ...], weights: tuple[float, ...]
) -> str:
    """Draw one item from an explicitly verified equal-weight distribution."""
    if len(options) != len(weights) or set(weights) != {1 / 5}:
        raise ValueError("Required category/status weights must each equal 1/5")
    # choice preserves the original seeded stream and is equivalent to weights 1/5 each.
    return generator.choice(options)


def _build_dataset() -> list[dict[str, Any]]:
    """Generate all fields from one seeded stream so output is repeatable."""
    generator = random.Random(SEED)

    # Seeded shuffling keeps mandatory coverage while avoiding fixed record positions.
    category_assignments = [
        category
        for category in REQUIRED_CATEGORIES
        for _ in range(3)
    ]
    category_assignments.extend(
        _equal_weight_choice(generator, REQUIRED_CATEGORIES, CATEGORY_WEIGHTS)
        for _ in range(RECORD_COUNT - len(category_assignments))
    )
    generator.shuffle(category_assignments)

    status_assignments = list(REQUIRED_STATUSES)
    status_assignments.extend(
        _equal_weight_choice(generator, REQUIRED_STATUSES, STATUS_WEIGHTS)
        for _ in range(RECORD_COUNT - len(status_assignments))
    )
    generator.shuffle(status_assignments)

    records = []
    for record_number in range(1, RECORD_COUNT + 1):
        records.append(
            {
                "record_id": f"LA-{record_number:03d}",
                "category": category_assignments[record_number - 1],
                "status": status_assignments[record_number - 1],
                "loan_amount_inr": generator.randint(
                    MIN_LOAN_AMOUNT_INR, MAX_LOAN_AMOUNT_INR
                ),
                "days_since_created": generator.randint(0, MAX_DAYS_SINCE_CREATED),
                "flagged_for_fraud_review": generator.random() < FRAUD_PROBABILITY,
            }
        )
    return records


def validate_dataset(records: list[dict[str, Any]]) -> None:
    """Raise ValueError with the failed requirement when data is invalid."""
    if len(records) != RECORD_COUNT:
        raise ValueError(f"Expected {RECORD_COUNT} records, found {len(records)}")

    required_fields = {
        "record_id",
        "category",
        "status",
        "loan_amount_inr",
        "days_since_created",
        "flagged_for_fraud_review",
    }
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each dataset entry must be a dictionary")
        missing_fields = required_fields - record.keys()
        if missing_fields:
            raise ValueError(
                f"Record {record.get('record_id', '<unknown>')} is missing: "
                f"{', '.join(sorted(missing_fields))}"
            )
        if record["category"] not in REQUIRED_CATEGORIES:
            raise ValueError(f"Invalid category: {record['category']}")
        if record["status"] not in REQUIRED_STATUSES:
            raise ValueError(f"Invalid status: {record['status']}")
        if (
            not isinstance(record["loan_amount_inr"], int)
            or isinstance(record["loan_amount_inr"], bool)
        ):
            raise ValueError("loan_amount_inr must be an integer")
        if not MIN_LOAN_AMOUNT_INR <= record["loan_amount_inr"] <= MAX_LOAN_AMOUNT_INR:
            raise ValueError(f"Loan amount is out of range: {record['loan_amount_inr']}")
        if (
            not isinstance(record["days_since_created"], int)
            or isinstance(record["days_since_created"], bool)
            or not (
            0 <= record["days_since_created"] <= MAX_DAYS_SINCE_CREATED
            )
        ):
            raise ValueError(
                f"Invalid days_since_created: {record['days_since_created']}"
            )
        if not isinstance(record["flagged_for_fraud_review"], bool):
            raise ValueError("flagged_for_fraud_review must be boolean")

    record_ids = [record["record_id"] for record in records]
    if len(set(record_ids)) != RECORD_COUNT:
        raise ValueError("record_id values must be unique")

    category_counts = Counter(record["category"] for record in records)
    for category in REQUIRED_CATEGORIES:
        if category_counts[category] < 3:
            raise ValueError(
                f"Category coverage failed for {category}: "
                f"found {category_counts[category]}, need at least 3"
            )

    status_counts = Counter(record["status"] for record in records)
    for status in REQUIRED_STATUSES:
        if status_counts[status] < 1:
            raise ValueError(f"Status coverage failed for {status}")

    fraud_count = sum(record["flagged_for_fraud_review"] for record in records)
    fraud_percentage = fraud_count / len(records) * 100
    if not 10 <= fraud_percentage <= 30:
        raise ValueError(
            "Fraud-review percentage must be between 10% and 30%; "
            f"found {fraud_percentage:.2f}%"
        )


LOAN_APPLICATIONS = _build_dataset()
validate_dataset(LOAN_APPLICATIONS)


def _print_report() -> None:
    """Print the required coverage and fraud summary."""
    category_counts = Counter(record["category"] for record in LOAN_APPLICATIONS)
    status_counts = Counter(record["status"] for record in LOAN_APPLICATIONS)
    fraud_count = sum(
        record["flagged_for_fraud_review"] for record in LOAN_APPLICATIONS
    )
    fraud_percentage = fraud_count / len(LOAN_APPLICATIONS) * 100

    print("Category counts:")
    for category in REQUIRED_CATEGORIES:
        print(f"  {category}: {category_counts[category]}")
    print("Status counts:")
    for status in REQUIRED_STATUSES:
        print(f"  {status}: {status_counts[status]}")
    print(f"Fraud percentage: {fraud_percentage:.2f}% ({fraud_count}/{RECORD_COUNT})")


if __name__ == "__main__":
    _print_report()
