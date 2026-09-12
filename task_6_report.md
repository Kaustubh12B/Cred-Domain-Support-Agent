# Cred Capstone Task 6 Report

- LLM mode: `MOCK_LLM (no external API calls)`
- Generated applications scored: 50

## Exact escalation formula

`escalation_score = 0.70 * fraud_flag + 0.30 * (1 - days_since_created / 30)`

`fraud_flag` is 1.0 for a fraud-review flag and 0.0 otherwise. A flagged, newly created application therefore reaches 1.0, while an unflagged application at 30 days reaches 0.0.

## Score distribution

- `0.0000`: 4 application(s)
- `0.0100`: 1 application(s)
- `0.0300`: 1 application(s)
- `0.0400`: 2 application(s)
- `0.0500`: 2 application(s)
- `0.0800`: 2 application(s)
- `0.0900`: 1 application(s)
- `0.1000`: 3 application(s)
- `0.1100`: 1 application(s)
- `0.1400`: 2 application(s)
- `0.1500`: 2 application(s)
- `0.1600`: 1 application(s)
- `0.1800`: 3 application(s)
- `0.1900`: 1 application(s)
- `0.2000`: 1 application(s)
- `0.2200`: 3 application(s)
- `0.2300`: 1 application(s)
- `0.2400`: 2 application(s)
- `0.2500`: 2 application(s)
- `0.2600`: 1 application(s)
- `0.2700`: 1 application(s)
- `0.2800`: 2 application(s)
- `0.2900`: 1 application(s)
- `0.3000`: 3 application(s)
- `0.7300`: 1 application(s)
- `0.8000`: 1 application(s)
- `0.8200`: 1 application(s)
- `0.8800`: 1 application(s)
- `0.9100`: 2 application(s)
- `0.9300`: 1 application(s)

## Escalation threshold

The nearest-rank 80th-percentile threshold is **0.2900**.
11 of 50 generated applications have scores at or above this threshold. This selects the highest-risk approximately 20% of the generated set; equal scores at the boundary can include additional records.
