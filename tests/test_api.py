import asyncio
import json

import httpx

from ichi_mcp import api

CURRENT = {
    "observation_type": "CURRENT_ICHI_EVALUATION",
    "headline_state": "LIVE",
    "headline_reason": None,
    "impaired_sources": [],
    "stale_inputs": ["phishing"],
    "age_seconds": 120,
    "cadence_minutes": 10,
    "served_at": "2026-10-31T13:28:35.307Z",
    "current": {
        "evaluation_id": "ev-test",
        "epoch": "2026-10-31T13:20:00.000Z",
        "completed_at": "2026-10-31T13:20:26.513Z",
        "model": "v7.1",
        "score": 65.01,
        "rounded": 65,
        "band": "ELEVATED",
        "dimensions": {"V": 42.78, "E": 55.75, "P": 36.73, "Z": 1},
        "contributions": {"V": 8.11},
        "informational": {"O": 29.98},
        "completeness": {"state": "COMPLETE"},
    },
}

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>ICHI test</title><description>d</description>
<lastBuildDate>Sat, 31 Oct 2026 12:57:05 GMT</lastBuildDate>
<item><title>A</title><link>https://ichi.global/alert?id=a</link><guid>a</guid>
<pubDate>Wed, 28 Oct 2026 21:57:05 GMT</pubDate><category>ADVISORY</category><description>x</description></item>
<item><title>B</title><link>https://ichi.global/alert?id=b</link><guid>b</guid></item>
<item><title>C</title><guid>c</guid></item>
</channel></rss>"""

HEALTH = {
    "status": "live",
    "confidence": "High",
    "updated": "2026-10-31T13:28:39.866Z",
    "feeds": {"resolved": 28, "total": 28, "failed": 0, "extra": "ignored"},
    "includedInScore": ["cves", "kev"],
    "failedFeeds": [{"key": "x", "name": "Feed X"}, "y"],
    "notConnected": [{"key": "greynoise", "name": "GreyNoise Event Feed"}],
}


def transport(routes):
    def handler(request: httpx.Request) -> httpx.Response:
        route = routes.get(request.url.path)
        if route is None:
            return httpx.Response(404)
        if isinstance(route, Exception):
            raise route
        if isinstance(route, bytes):
            return httpx.Response(200, content=route)
        return httpx.Response(200, content=json.dumps(route).encode())

    return httpx.MockTransport(handler)


def run(coro):
    return asyncio.run(coro)


def test_current_index_maps_fields():
    out = run(api.get_current_index(transport({"/api/current-index": CURRENT})))
    assert out["ok"] is True
    assert out["score"] == 65.01 and out["band"] == "ELEVATED" and out["band_range"] == "50-69"
    assert out["evaluated_at"] == "2026-10-31T13:20:26.513Z"
    dims = {d["key"]: d for d in out["dimensions"]}
    assert dims["V"]["name"] == "Vulnerability Pressure" and dims["V"]["contribution"] == 8.11
    assert dims["P"]["name"].startswith("Actor Operations")
    assert dims["Z"]["name"] == "Z"  # unknown keys pass through
    assert out["freshness"]["stale_inputs"] == ["phishing"]
    assert out["freshness"]["completeness"] == "COMPLETE"
    assert out["link"] == "https://ichi.global"


def test_current_index_missing_current():
    out = run(api.get_current_index(transport({"/api/current-index": {"headline_state": "LIVE"}})))
    assert out["ok"] is False and "current" in out["error"]


def test_http_error_is_graceful():
    out = run(api.get_current_index(transport({})))
    assert out == {"ok": False, "error": out["error"], "link": "https://ichi.global"}
    assert "HTTP 404" in out["error"]


def test_timeout_is_graceful():
    exc = httpx.ReadTimeout("slow")
    out = run(api.get_source_health(transport({"/api/health": exc})))
    assert out["ok"] is False and "timed out" in out["error"]


def test_invalid_json_is_graceful():
    out = run(api.get_current_index(transport({"/api/current-index": b"<html>"})))
    assert out["ok"] is False and "invalid JSON" in out["error"]


def test_alerts_parse_and_limit():
    out = run(api.get_recent_alerts(2, transport({"/api/alerts": RSS})))
    assert out["ok"] is True and out["count"] == 2
    first = out["items"][0]
    assert first["title"] == "A" and first["category"] == "ADVISORY"
    assert first["published"].startswith("2026-10-28T21:57:05")
    assert out["items"][1]["published"] is None


def test_alerts_bad_xml():
    out = run(api.get_recent_alerts(5, transport({"/api/alerts": b"not xml"})))
    assert out["ok"] is False and "parse" in out["error"]


def test_alerts_limit_clamped():
    out = run(api.get_recent_alerts(0, transport({"/api/alerts": RSS})))
    assert out["count"] == 1
    out = run(api.get_recent_alerts("nope", transport({"/api/alerts": RSS})))
    assert out["count"] == 3


def test_health_summary():
    out = run(api.get_source_health(transport({"/api/health": HEALTH})))
    assert out["ok"] is True and out["status"] == "live"
    assert out["feeds"] == {"resolved": 28, "total": 28, "failed": 0}
    assert out["failed_feeds"] == ["Feed X", "y"]
    assert out["not_connected"] == ["GreyNoise Event Feed"]
