"""Exercise the server end-to-end over stdio using the official MCP client.

Usage:  python examples/smoke_client.py            (uses `ichi-mcp` on PATH)
        python examples/smoke_client.py uvx --from git+https://github.com/bernik-bot/ichi-mcp ichi-mcp
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _payload(result):
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if structured:
        return structured.get("result", structured)
    texts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
    return json.loads(texts[0]) if texts else None


async def main(cmd):
    params = StdioServerParameters(command=cmd[0], args=cmd[1:], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])
            for name, args in [
                ("get_current_index", {}),
                ("get_recent_alerts", {"limit": 3}),
                ("get_source_health", {}),
            ]:
                result = await session.call_tool(name, args)
                is_error = getattr(result, "isError", getattr(result, "is_error", None))
                print(f"\n== {name} {args} (isError={is_error})")
                print(json.dumps(_payload(result), indent=2)[:4000])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["ichi-mcp"]))
