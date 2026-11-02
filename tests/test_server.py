import asyncio

from ichi_mcp.server import mcp


def test_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == ["get_current_index", "get_recent_alerts", "get_source_health"]


def _hint(a, camel, snake):
    # mcp 1.x exposes camelCase attributes, mcp 2.x snake_case (the wire format is camelCase in both)
    return getattr(a, camel, None) if hasattr(a, camel) else getattr(a, snake, None)


def test_every_tool_is_declared_read_only():
    # directories (Glama) and clients read these hints: every tool only GETs ICHI's public API
    for t in asyncio.run(mcp.list_tools()):
        a = t.annotations
        assert a is not None, t.name
        assert _hint(a, "readOnlyHint", "read_only_hint") is True, t.name
        assert _hint(a, "destructiveHint", "destructive_hint") is False, t.name
        assert _hint(a, "idempotentHint", "idempotent_hint") is True, t.name
        assert _hint(a, "openWorldHint", "open_world_hint") is True, t.name
        assert a.title, t.name
    # and on the wire (what a client receives) the hints are camelCase in both SDK versions
    wire = asyncio.run(mcp.list_tools())[0].annotations.model_dump(by_alias=True, exclude_none=True)
    assert wire.get("readOnlyHint") is True and wire.get("destructiveHint") is False, wire


def _schema(t):
    return getattr(t, "inputSchema", None) or getattr(t, "input_schema", None) or {}


def test_tools_have_descriptions_and_schemas():
    # introspection: each tool states what it does and takes only declared, simple arguments
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    for t in tools.values():
        assert t.description and len(t.description) > 40, t.name
        assert _schema(t).get("type") == "object", t.name
    assert set(_schema(tools["get_recent_alerts"]).get("properties", {})) == {"limit"}
    assert _schema(tools["get_current_index"]).get("properties", {}) == {}


def test_the_client_only_reads():
    # read-only by construction: the API client issues GET requests only
    import inspect

    from ichi_mcp import api

    src = inspect.getsource(api)
    assert "client.get(" in src
    for verb in ("client.post(", "client.put(", "client.patch(", "client.delete(", "client.request("):
        assert verb not in src, verb
