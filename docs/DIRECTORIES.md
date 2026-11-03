# Directory listings: status and submission text

Status, 2026-11-03: **ready for submission. Not listed in any directory.** Nothing here says "listed" or "verified" until
the directory itself confirms it. Every submission is an owner action (an external publication); nothing is submitted
from this repository.

## Listing text (all directories)

**Name:** ICHI - Internet Cyber Health Index

**Short description:** Read-only MCP server for the free ICHI public API: the live internet-wide cyber threat score, its
band and dimensions, recent critical-vulnerability advisories, and source health. No API key.

**Long description:** ICHI (https://ichi.global) is a free, source-transparent barometer of internet-wide cyber threat
conditions, scored with the published VECTORS model from public sources (NVD, CISA KEV, FIRST EPSS, abuse.ch and others).
This server exposes three read-only tools over stdio. Each answer carries ICHI's own timestamps and an attribution line.
ICHI is an outside-in directional signal - not an organization-specific risk score or a forecast.

**Tools**

| Tool | Returns | Timestamps |
|---|---|---|
| `get_current_index` | score 0-100, band and its range, the seven dimensions with names and contributions, model version, freshness and impaired inputs (null = not stated, never "none") | `evaluated_at`, `epoch`, `freshness.served_at` |
| `get_recent_alerts(limit=5)` | the latest critical-advisory items: title, link, published time, category, description | `published`, `last_build` |
| `get_source_health` | overall status and confidence, feed counts, the feeds that are failed, stale, delayed or not connected, and which feeds feed the score | `updated` |

**Example prompts**
- "What is the ICHI score right now, and which dimensions are driving it?"
- "Has ICHI published any critical vulnerability advisories in the last day?"
- "Are any of ICHI's sources stale or failing? Can I trust today's reading?"

**Attribution and acceptable use:** data from ICHI - Internet Cyber Health Index (https://ichi.global); methodology at
https://ichi.global/methodology. Keep the attribution line that every answer carries. Respect the API's cache headers
(the score changes every 10 minutes). Do not present ICHI as an organization-specific risk score. The server sends no
key and keeps no state.

**Safety:** read-only (MCP annotations `readOnlyHint: true`, `destructiveHint: false`), HTTP GET only, to public
`ichi.global` endpoints, no secrets, no writes, non-root container.

## Per directory

| Directory | Needs | Ready here | Owner action |
|---|---|---|---|
| Glama (glama.ai/mcp/servers) | public repo, license, `glama.json` with maintainers, a Dockerfile that starts the stdio server and lists its tools | yes: MIT, `glama.json` (`bernik-bot`), Dockerfile; CI builds it and lists the tools | sign in with GitHub as `bernik-bot`; Add Server (or Claim it if it was discovered): `https://github.com/bernik-bot/ichi-mcp`; in the listing's admin page choose the Dockerfile build (no env vars); create a Glama release (a GitHub release alone does not clear "No release"); wait for its checks. Glama's own site does not document these steps; they follow its admin pages and community checklists |
| Official MCP Registry (registry.modelcontextprotocol.io, preview) | the package published first (PyPI), with its ownership marker; a `server.json`; `mcp-publisher login github` then `publish` | `server.json` template; the README carries `mcp-name: io.github.bernik-bot/ichi-mcp` (the PyPI ownership marker) | publish `ichi-mcp` 0.1.2 to PyPI (owner account); then `mcp-publisher validate` and `mcp-publisher publish`. Publishing is effectively permanent |
| PulseMCP | a public repo; it also ingests from the official registry | listing text above | submit via pulsemcp.com/submit, or wait for registry ingestion |
| mcp.so | a public repo URL and a description | listing text above | submit via mcp.so's Submit page (GitHub sign-in) |
| Smithery | a `smithery.yaml` for local stdio servers, or a hosted HTTP endpoint | not prepared: it would need a runtime config file; a hosted endpoint would be a new service | decide whether to list there; then a `smithery.yaml` PR |

The Glama badge goes in the README only after the listing exists and passes its checks.
