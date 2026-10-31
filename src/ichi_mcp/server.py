"""MCP stdio server exposing the public ICHI API as tools."""

from __future__ import annotations

import logging
from typing import Any

try:  # mcp >= 2: FastMCP was renamed MCPServer
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import api

INSTRUCTIONS = "Tools for the ICHI (Internet Cyber Health Index, https://ichi.global) public API. " + api.POSITIONING

mcp = _Server("ichi", instructions=INSTRUCTIONS)


@mcp.tool()
async def get_current_index() -> dict[str, Any]:
    """Get the current ICHI score (0-100), band (NORMAL/GUARDED/ELEVATED/HIGH/CRITICAL),
    per-dimension sub-scores with human-readable names, and freshness/impairment info.

    ICHI is an outside-in, internet-wide directional signal - not an
    organization-specific risk score or a forecast.
    """
    return await api.get_current_index()


@mcp.tool()
async def get_recent_alerts(limit: int = 5) -> dict[str, Any]:
    """Get the latest items (default 5, max 50) from ICHI's critical-advisory RSS feed
    (https://ichi.global/api/alerts): title, link, published time, category, description."""
    return await api.get_recent_alerts(limit)


@mcp.tool()
async def get_source_health() -> dict[str, Any]:
    """Summarize ICHI's source health (https://ichi.global/api/health): overall status,
    confidence, live/stale/failed feed counts, and which sources feed the score."""
    return await api.get_source_health()


def main() -> None:
    # httpx logs every request at INFO; keep stderr quiet unless something goes wrong.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
