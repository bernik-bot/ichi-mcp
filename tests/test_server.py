import asyncio

from ichi_mcp.server import mcp


def test_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == ["get_current_index", "get_recent_alerts", "get_source_health"]
