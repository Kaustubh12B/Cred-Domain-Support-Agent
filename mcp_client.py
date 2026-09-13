"""Task 14 FastMCP HTTP client and report generator."""

import asyncio
import json
from pathlib import Path

from fastmcp import Client

from loan_application_status import MOCK_LLM


PROJECT_DIR = Path(__file__).resolve().parent
MCP_URL = "http://127.0.0.1:8000/mcp"


async def run_client() -> list[dict]:
    """Connect to the separately running HTTP MCP server and make two tool calls."""
    responses: list[dict] = []
    async with Client(MCP_URL) as client:
        for record_id in ("LA-001", "LA-002"):
            result = await client.call_tool("get_loan_status", {"record_id": record_id})
            responses.append(
                {
                    "tool": "get_loan_status",
                    "arguments": {"record_id": record_id},
                    "is_error": result.is_error,
                    "structured_content": result.data,
                }
            )
    return responses


def write_report(responses: list[dict]) -> None:
    response_lines = "\n".join(
        f"### Call {index}\n\n```json\n{json.dumps(response, indent=2)}\n```"
        for index, response in enumerate(responses, start=1)
    )
    (PROJECT_DIR / "task_14_mcp_responses.json").write_text(
        json.dumps(responses, indent=2), encoding="utf-8"
    )
    (PROJECT_DIR / "task_14_fastmcp_report.md").write_text(
        "\n".join(
            [
                "# Cred Capstone Task 14 FastMCP HTTP Report",
                "",
                f"- LLM mode: `{MOCK_LLM}`; no external LLM or API is called.",
                "- FastMCP server endpoint: `http://127.0.0.1:8000/mcp`.",
                "- Server command: `python mcp_server.py`.",
                "- Separate client command: `python mcp_client.py`.",
                "- Tool: `get_loan_status(record_id)`, backed by the deterministic Task 6 dataset.",
                "- Each response below is the standardized client envelope: tool name, arguments, "
                "MCP error flag, and structured tool content.",
                "",
                "## Successful HTTP MCP responses",
                "",
                response_lines,
                "",
                "Both HTTP MCP calls returned `is_error: false` for distinct loan-status IDs.",
                "",
            ]
        ),
        encoding="utf-8",
    )


async def main() -> None:
    responses = await run_client()
    write_report(responses)
    print(json.dumps(responses, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
