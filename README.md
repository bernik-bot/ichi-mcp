# ichi-mcp

[![ci](https://github.com/bernik-bot/ichi-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/bernik-bot/ichi-mcp/actions/workflows/ci.yml)
[![Internet cyber health](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fichi.global%2Fapi%2Fcurrent-index&query=%24.current.band&label=Internet%20cyber%20health)](https://ichi.global)

A minimal [Model Context Protocol](https://modelcontextprotocol.io) (MCP) stdio
server, built on the official Python `mcp` SDK, that lets an AI assistant read
the free public [ICHI](https://ichi.global) API. No API key is needed.

## What ICHI is (and is not)

ICHI — the Internet Cyber Health Index — is a free, publicly accessible,
source-transparent daily barometer of internet-wide cyber threat conditions,
created by Joe Bernik. It is an **outside-in directional signal**. It is
**not** an organization-specific risk score, not a deterministic forecast, and
not a substitute for your own internal telemetry. The band is the operative
read; moves within a band should be treated as noise. See the
[methodology](https://ichi.global/methodology).

This repository is maintained by/for ICHI's creator.

## Tools

| Tool | Source | Returns |
|---|---|---|
| `get_current_index` | `GET /api/current-index` | score, rounded score, band + band range, evaluation time, model, per-dimension sub-scores with human-readable names and contributions, informational (unscored) values, freshness/impairment info (headline state, age, stale/impaired/invalid inputs, degraded dimensions), links |
| `get_recent_alerts(limit=5)` | `GET /api/alerts` (RSS 2.0) | latest N (1–50) items from ICHI's critical-advisory feed: title, link, id, published (ISO-8601), category, description |
| `get_source_health` | `GET /api/health` | overall status and confidence, feed counts (live/stale/delayed/failed, by tier), sources included in the score, and names of failed/stale/delayed/dormant/not-connected feeds |

Every tool returns a JSON object with `"ok": true`, or `"ok": false` plus an
`"error"` message on timeouts, HTTP errors, or unparseable responses — the
server never crashes on a bad upstream response.

## Install / run

Requires Python ≥ 3.10. With [uv](https://docs.astral.sh/uv/):

```bash
uvx --from git+https://github.com/bernik-bot/ichi-mcp ichi-mcp
```

Pin a release with `git+https://github.com/bernik-bot/ichi-mcp@v0.1.0`.
Or with pip: `pip install git+https://github.com/bernik-bot/ichi-mcp` then run `ichi-mcp`.
(Not published on PyPI.)

### Claude Desktop

Add to `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ichi": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/bernik-bot/ichi-mcp", "ichi-mcp"]
    }
  }
}
```

If `uvx` isn't on Claude Desktop's PATH, use its absolute path (`which uvx`).

### Generic MCP client (stdio)

```json
{
  "command": "uvx",
  "args": ["--from", "git+https://github.com/bernik-bot/ichi-mcp", "ichi-mcp"],
  "env": { "ICHI_TIMEOUT": "10" }
}
```

### Docker

```bash
docker build -t ichi-mcp .
docker run -i --rm ichi-mcp          # stdio: point an MCP client at this command
```

The image runs as a non-root user, needs no secrets, volumes or ports, and only makes outbound HTTPS GET requests to
`ichi.global`. `python examples/introspect.py docker run -i --rm ichi-mcp` starts it, initializes, and lists the tools
(no tool is called, so no network is needed); CI runs exactly that.

### Read-only

Every tool only reads ICHI's public API (HTTP GET, no API key, no state) and is declared so in its MCP annotations:
`readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true`, `openWorldHint: true`.

### Glama

`glama.json` names the maintainer (`bernik-bot`) so the listing can be claimed on [Glama](https://glama.ai/mcp/servers).
Glama builds the `Dockerfile`, starts the server and lists its tools; the score badge is added here once the listing exists.

### Configuration

| Env var | Default | Meaning |
|---|---|---|
| `ICHI_TIMEOUT` | `10` | HTTP timeout in seconds |
| `ICHI_BASE_URL` | `https://ichi.global` | API base URL (testing only) |

## Example output (abridged, from a live call)

```json
{
  "ok": true,
  "score": 64.91,
  "rounded": 65,
  "band": "ELEVATED",
  "band_range": "50-69",
  "evaluated_at": "2026-10-31T13:30:22.978Z",
  "model": "v7.1",
  "dimensions": [
    {"key": "V", "name": "Vulnerability Pressure", "score": 42.21, "contribution": 8},
    {"key": "C", "name": "C2 / Malware Infrastructure", "score": 96.03, "contribution": 13.14}
  ],
  "freshness": {"headline_state": "LIVE", "age_seconds": 267, "completeness": "COMPLETE", "stale_inputs": [], "impaired_sources": []},
  "link": "https://ichi.global"
}
```

## Limitations

- Reads only ICHI's public endpoints; it does no scoring of its own and adds no data.
- Dimension names are mapped from API keys using the published methodology
  (model v7.x). The API key `P` is the phishing-driven dimension the methodology
  labels "O — Actor Operations"; the informational `O` value is labelled as
  Outages. Unknown keys are passed through unchanged. If ICHI's schema changes,
  missing fields come back as `null` rather than errors.
- The alerts feed is ICHI's critical-advisory RSS feed; per its own description
  it is observation only and carries no score.
- No caching: each tool call makes one HTTP request. ICHI's current index is
  re-evaluated about every 10 minutes.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
ruff check . && pytest -q                 # tests mock HTTP, no network
python examples/smoke_client.py           # live end-to-end over stdio via the MCP client
```

Works with both `mcp` 1.x (`FastMCP`) and 2.x (`MCPServer`, the renamed FastMCP);
CI tests both.

## License

MIT
