# Cred Capstone Task 16 Retry and Timeout Report

- LLM mode: `MOCK_LLM (no external API calls)`; no external LLM or API is called.
- Retry policy: Tenacity retries only `TransientRiskServiceError`; max attempts = 3; exponential-backoff initial interval = 0.05 seconds; max interval = 0.20 seconds; jitter = disabled for deterministic reproducibility.
- Retry result: `risk lookup succeeded` after `3` attempts (first two attempts intentionally failed).
- Observed deterministic backoff intervals before recovery: `[0.05, 0.1]` seconds.
- Per-node timeout: a 50 ms node operation is bounded by `asyncio.wait_for(..., timeout=0.01)` inside the node.
- Per-node demonstration result: `per_node_timeout`.
- Global timeout: the entire compiled graph invocation containing a 50 ms node is bounded by `asyncio.wait_for(..., timeout=0.01)`.
- Global demonstration result: `global_timeout`.

The scopes differ deliberately: the per-node timeout is handled as a node outcome, while the global timeout cancels the graph invocation itself.
