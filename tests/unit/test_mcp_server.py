"""Unit tests for Model Context Protocol (MCP) Server and Agent Projections (ADR D014)."""

import json
from pathlib import Path
import pytest

from masar.agent_control import AgentControlPlane
from masar.mcp_server import MasarMcpServer


def test_agent_control_plane_manifest_and_diagnose(mock_db_path):
    """Verify machine manifest and diagnostics projections."""
    control = AgentControlPlane(db_path=mock_db_path)
    manifest = control.get_manifest()

    assert manifest["product"] == "Masar"
    assert "tools" in manifest
    assert "masar_search" in manifest["tools"]

    diag = control.diagnose()
    assert diag["status"] == "HEALTHY"
    assert diag["record_count"] == 6


def test_mcp_server_tools_list():
    """Verify MCP tools/list returns compliant schemas."""
    server = MasarMcpServer()
    tools = server.list_tools()

    tool_names = [t["name"] for t in tools]
    assert "masar_search" in tool_names
    assert "masar_inspect" in tool_names
    assert "masar_adjust_split" in tool_names
    assert "masar_add_manual" in tool_names
    assert "masar_diagnose" in tool_names

    search_tool = next(t for t in tools if t["name"] == "masar_search")
    assert "inputSchema" in search_tool
    assert "seed" in search_tool["inputSchema"]["properties"]


def test_mcp_server_call_search_and_inspect(mock_db_path):
    """Verify MCP tools/call executes and returns structured JSON text."""
    server = MasarMcpServer(db_path=mock_db_path)

    # Tool call: masar_search
    res_search = server.call_tool(
        "masar_search",
        {"seed": "إنما الأعمال بالنيات", "scope": "all", "limit": 5},
    )
    assert not res_search.get("isError", False)
    content = json.loads(res_search["content"][0]["text"])
    assert isinstance(content, list)
    assert len(content) > 0

    # Tool call: masar_inspect
    res_inspect = server.call_tool(
        "masar_inspect",
        {"hadith_id": "1"},
    )
    assert not res_inspect.get("isError", False)
    cand = json.loads(res_inspect["content"][0]["text"])
    assert cand["id"] == "1"
    assert "إنما الأعمال بالنيات" in cand["matn"]
