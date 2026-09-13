"""Task 14 FastMCP HTTP server for the local Cred loan-status tool."""

from fastmcp import FastMCP

from loan_application_status import check_loan_application_status


mcp = FastMCP("Cred loan-status MCP server")


@mcp.tool
def get_loan_status(record_id: str) -> dict:
    """Return the deterministic local status and escalation score for an LA ID."""
    return check_loan_application_status(record_id.upper())


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
