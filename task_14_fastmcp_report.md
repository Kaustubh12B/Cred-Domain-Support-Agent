# Cred Capstone Task 14 FastMCP HTTP Report

- LLM mode: `MOCK_LLM (no external API calls)`; no external LLM or API is called.
- FastMCP server endpoint: `http://127.0.0.1:8000/mcp`.
- Server command: `python mcp_server.py`.
- Separate client command: `python mcp_client.py`.
- Tool: `get_loan_status(record_id)`, backed by the deterministic Task 6 dataset.
- Each response below is the standardized client envelope: tool name, arguments, MCP error flag, and structured tool content.

## Successful HTTP MCP responses

### Call 1

```json
{
  "tool": "get_loan_status",
  "arguments": {
    "record_id": "LA-001"
  },
  "is_error": false,
  "structured_content": {
    "record_id": "LA-001",
    "status": "Approved",
    "loan_amount_inr": 1579678,
    "escalation_score": 0.18999999999999997
  }
}
```
### Call 2

```json
{
  "tool": "get_loan_status",
  "arguments": {
    "record_id": "LA-002"
  },
  "is_error": false,
  "structured_content": {
    "record_id": "LA-002",
    "status": "Approved",
    "loan_amount_inr": 4876353,
    "escalation_score": 0.9099999999999999
  }
}
```

Both HTTP MCP calls returned `is_error: false` for distinct loan-status IDs.
