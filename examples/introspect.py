"""Start the server over stdio, initialize, list its tools, and check them: what an MCP directory (Glama) does.

No tool is called, so no network is needed.

Usage:  python examples/introspect.py                                  (uses `ichi-mcp` on PATH)
        python examples/introspect.py docker run -i --rm ichi-mcp      (the Docker image)
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED = {"get_current_index", "get_recent_alerts", "get_source_health"}


async def main(cmd: list[str]) -> int:
    params = StdioServerParameters(command=cmd[0], args=cmd[1:], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await asyncio.wait_for(session.initialize(), timeout=30)
            info = getattr(init, "serverInfo", None) or getattr(init, "server_info", None)
            print("server:", getattr(info, "name", None), getattr(info, "version", None))
            tools = (await asyncio.wait_for(session.list_tools(), timeout=30)).tools
            names = {t.name for t in tools}
            print("tools:", sorted(names))
            problems = []
            if names != EXPECTED:
                problems.append(f"tools {sorted(names)} != {sorted(EXPECTED)}")
            for t in tools:
                a = t.annotations.model_dump(by_alias=True, exclude_none=True) if t.annotations else {}
                if not (a.get("readOnlyHint") is True and a.get("destructiveHint") is False):
                    problems.append(f"{t.name}: not declared read-only")
                if not t.description:
                    problems.append(f"{t.name}: no description")
            for p in problems:
                print("FAIL", p)
            print("ok" if not problems else "introspection failed")
            return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or ["ichi-mcp"])))
