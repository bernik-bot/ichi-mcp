"""Thin, dependency-light client for the public ICHI API (https://ichi.global).

Every public function returns a plain ``dict``. Network/parse failures never
raise out of these functions: they return ``{"ok": False, "error": "..."}`` so
an MCP client gets a readable message instead of a stack trace.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from . import __version__

BASE_URL = os.environ.get("ICHI_BASE_URL", "https://ichi.global").rstrip("/")
try:
    TIMEOUT = float(os.environ.get("ICHI_TIMEOUT", "10"))
except ValueError:  # pragma: no cover - defensive
    TIMEOUT = 10.0

SITE = "https://ichi.global"
METHODOLOGY = "https://ichi.global/methodology"

POSITIONING = (
    "ICHI is a free, source-transparent barometer of internet-wide cyber threat "
    "conditions. It is an outside-in directional signal - not an organization-"
    "specific risk score, not a deterministic forecast, and not a substitute for "
    "internal telemetry. The band is the operative read; treat moves within a band "
    "as noise."
)

# API dimension keys -> human-readable names, per https://ichi.global/methodology
# (model v7.x). The API key "P" is the phishing-driven dimension the methodology
# now labels "O - Actor Operations". Unknown keys are passed through unchanged.
DIMENSION_NAMES = {
    "V": "Vulnerability Pressure",
    "E": "Exploitation",
    "C": "C2 / Malware Infrastructure",
    "T": "Threat Actors",
    "R": "Ransomware",
    "S": "Supply Chain",
    "P": "Actor Operations (phishing-driven)",
}
INFORMATIONAL_NAMES = {
    "O": "Outages (informational, not scored)",
    "obsEcosystem": "Ecosystem observation (informational, not scored)",
}

BANDS = [
    ("NORMAL", 0, 24),
    ("GUARDED", 25, 49),
    ("ELEVATED", 50, 69),
    ("HIGH", 70, 84),
    ("CRITICAL", 85, 100),
]


def _err(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message, "link": SITE}


def _client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=httpx.Timeout(TIMEOUT),
        headers={"User-Agent": f"ichi-mcp/{__version__} (+https://github.com/bernik-bot/ichi-mcp)"},
        follow_redirects=True,
        transport=transport,
    )


async def _get(path: str, transport: httpx.AsyncBaseTransport | None = None) -> httpx.Response | str:
    """GET ``path``; return the response, or an error string on failure."""
    try:
        async with _client(transport) as client:
            resp = await client.get(path)
    except httpx.TimeoutException:
        return f"timed out after {TIMEOUT:g}s fetching {BASE_URL}{path}"
    except httpx.HTTPError as exc:
        return f"network error fetching {BASE_URL}{path}: {exc.__class__.__name__}: {exc}"
    if resp.status_code != 200:
        return f"HTTP {resp.status_code} from {BASE_URL}{path}"
    return resp


async def _get_json(path: str, transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any] | str:
    resp = await _get(path, transport)
    if isinstance(resp, str):
        return resp
    try:
        data = resp.json()
    except ValueError:
        return f"invalid JSON from {BASE_URL}{path}"
    if not isinstance(data, dict):
        return f"unexpected JSON shape from {BASE_URL}{path}"
    return data


def _band_range(band: str | None) -> str | None:
    for name, lo, hi in BANDS:
        if band == name:
            return f"{lo}-{hi}"
    return None


def _named(values: Any, names: dict[str, str], contributions: Any = None) -> list[dict[str, Any]]:
    if not isinstance(values, dict):
        return []
    contributions = contributions if isinstance(contributions, dict) else {}
    out = []
    for key, value in values.items():
        item: dict[str, Any] = {"key": key, "name": names.get(key, key), "score": value}
        if key in contributions:
            item["contribution"] = contributions[key]
        out.append(item)
    return out


async def get_current_index(transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    data = await _get_json("/api/current-index", transport)
    if isinstance(data, str):
        return _err(data)
    cur = data.get("current")
    if not isinstance(cur, dict) or cur.get("score") is None:
        return _err("response has no current evaluation (current.score missing)")

    band = cur.get("band")
    completeness = cur.get("completeness") if isinstance(cur.get("completeness"), dict) else {}
    return {
        "ok": True,
        "score": cur.get("score"),
        "rounded": cur.get("rounded"),
        "band": band,
        "band_range": _band_range(band),
        "evaluated_at": cur.get("completed_at") or cur.get("built_at") or cur.get("epoch"),
        "epoch": cur.get("epoch"),
        "model": cur.get("model"),
        "evaluation_id": cur.get("evaluation_id"),
        "dimensions": _named(cur.get("dimensions"), DIMENSION_NAMES, cur.get("contributions")),
        "informational": _named(cur.get("informational"), INFORMATIONAL_NAMES),
        "freshness": {
            "headline_state": data.get("headline_state"),
            "headline_reason": data.get("headline_reason"),
            "age_seconds": data.get("age_seconds"),
            "cadence_minutes": data.get("cadence_minutes"),
            "stale_after_minutes": data.get("stale_after_minutes"),
            "served_at": data.get("served_at"),
            "completeness": completeness.get("state"),
            "impaired_sources": data.get("impaired_sources") or [],
            "stale_inputs": data.get("stale_inputs") or [],
            "invalid_inputs": data.get("invalid_inputs") or [],
            "degraded_dimensions": cur.get("degraded_dimensions") or [],
            "unavailable_dimensions": cur.get("unavailable_dimensions") or [],
        },
        "link": SITE,
        "methodology": METHODOLOGY,
        "note": POSITIONING,
    }


def _text(el: ET.Element | None, tag: str) -> str | None:
    if el is None:
        return None
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _iso(rfc822: str | None) -> str | None:
    if not rfc822:
        return None
    try:
        return parsedate_to_datetime(rfc822).isoformat()
    except (TypeError, ValueError):
        return rfc822


async def get_recent_alerts(limit: int = 5, transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = 5
    resp = await _get("/api/alerts", transport)
    if isinstance(resp, str):
        return _err(resp)
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        return _err(f"could not parse RSS from {BASE_URL}/api/alerts: {exc}")
    channel = root.find("channel")
    if channel is None:
        return _err("RSS feed has no <channel>")
    items = []
    for item in channel.findall("item")[:limit]:
        items.append(
            {
                "title": _text(item, "title"),
                "link": _text(item, "link"),
                "id": _text(item, "guid"),
                "published": _iso(_text(item, "pubDate")),
                "category": _text(item, "category"),
                "description": _text(item, "description"),
            }
        )
    return {
        "ok": True,
        "feed_title": _text(channel, "title"),
        "feed_description": _text(channel, "description"),
        "last_build": _iso(_text(channel, "lastBuildDate")),
        "count": len(items),
        "items": items,
        "feed_url": f"{SITE}/api/alerts",
        "link": f"{SITE}/alert",
    }


def _feed_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for v in value:
        if isinstance(v, dict):
            out.append(str(v.get("name") or v.get("key") or v))
        else:
            out.append(str(v))
    return out


async def get_source_health(transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    data = await _get_json("/api/health", transport)
    if isinstance(data, str):
        return _err(data)
    feeds = data.get("feeds") if isinstance(data.get("feeds"), dict) else {}
    keys = ("resolved", "total", "coreLive", "coreTotal", "stale", "delayed", "failed", "byTier")
    return {
        "ok": True,
        "status": data.get("status"),
        "confidence": data.get("confidence"),
        "updated": data.get("updated"),
        "feeds": {k: feeds[k] for k in keys if k in feeds},
        "included_in_score": data.get("includedInScore") or [],
        "failed_feeds": _feed_names(data.get("failedFeeds")),
        "stale_feeds": _feed_names(data.get("staleFeeds")),
        "delayed_feeds": _feed_names(data.get("delayedFeeds")),
        "coverage_drop_feeds": _feed_names(data.get("coverageDropFeeds")),
        "dormant_feeds": _feed_names(data.get("dormant")),
        "not_connected": _feed_names(data.get("notConnected")),
        "link": f"{SITE}/api/health",
    }
