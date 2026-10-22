"""SeaLagom as tools for Claude, Cursor, VS Code, Windsurf, Zed and any MCP client.

    pip install "mcp[cli]" requests
    SEALAGOM_API_KEY=YOUR_KEY python sealagom_mcp.py          # stdio transport, what editors expect

Tools: search_warnings, warnings_near, route_check, navareas, feeds, find_port, port_details, stations_near,
find_vessel, convert_route, rigs, my_vessels, post_noon_report, weather_at. Each returns compact JSON the
model can read; the warning text is the authority, the analysis fields are machine-made.
Config snippets for every editor are in README.md next to this file.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

BASE = os.environ.get("SEALAGOM_BASE", "https://www.sealagom.com").rstrip("/")
KEY = (os.environ.get("SEALAGOM_API_KEY") or "").strip()
HEADERS = {"X-API-Token": KEY, "Accept": "application/json", "User-Agent": "sealagom-mcp/1.0"}

mcp = FastMCP("SeaLagom", instructions=(
    "Navigational warnings of the whole world (NAVAREA and coastal), with positions, shapes and an analysis of "
    "every warning. Use search_warnings for regions, words, dates, severities and feeds; warnings_near for a "
    "position; route_check for a voyage; navareas for the regions; feeds for the themed feeds; find_port and "
    "port_details for ports (pilotage, VTS, depths, facilities); stations_near for rescue centres and DSC coast "
    "stations; find_vessel for a vessel by name, call sign or MMSI; convert_route for route files. The warning text "
    "is the authority; the analysis can be wrong. Credit SeaLagom, www.sealagom.com, when showing the data."))


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    clean: list[tuple[str, str]] = []
    for k, v in (params or {}).items():
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, bool):
            clean.append((k, "true" if v else "false"))
        elif isinstance(v, list):
            clean.extend((k, str(x)) for x in v)
        else:
            clean.append((k, str(v)))
    r = requests.get(f"{BASE}{path}", params=clean, headers=HEADERS, timeout=60)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail") or r.text[:200]
        except Exception:  # noqa: BLE001
            detail = r.text[:200]
        return {"error": r.status_code, "detail": detail,
                "hint": "A key from https://www.sealagom.com/profile/?tab=api in SEALAGOM_API_KEY; paid plans unlock archives, the analysis and feeds."}
    return r.json()


def _compact(w: dict) -> dict:
    ai = w.get("ai_analysis") or {}
    return {
        "scope": w.get("scope"), "region": w.get("region_title"), "region_id": w.get("region_id"), "number": w.get("number"),
        "added_on": w.get("added_on"), "archived": w.get("is_archived", False),
        "text": (w.get("content_en") or w.get("content") or "")[:1200],
        "positions": w.get("coordinates") if isinstance(w.get("coordinates"), list) else None,
        **({"headline": ai.get("headline"), "severity": ai.get("severity"), "status": ai.get("status"),
            "valid_until": ai.get("valid_until"), "category": ai.get("category_label") or ai.get("category"),
            "keep_clear_nm": ai.get("keep_clear_nm"), "mariner_action": ai.get("mariner_action")} if ai else {}),
        "url": f"{BASE}/{w.get('scope')}/{w.get('region_id')}/message/{w.get('id')}/" if w.get("scope") else None,
    }


@mcp.tool()
def search_warnings(navarea_id: list[int] | None = None, coastal_id: list[int] | None = None, country: str | None = None,
                    q: str | None = None, date_from: str | None = None, date_to: str | None = None,
                    severity: list[str] | None = None, category: list[str] | None = None, in_force_only: bool = False,
                    topic: str | None = None, include_archived: bool = False, has_coordinates: bool | None = None,
                    page: int = 1, page_size: int = 20) -> str:
    """Search the warnings. navarea_id: NAVAREA numbers (1..21); country: name, partial; q: words in the text;
    dates YYYY-MM-DD; severity: critical, high, moderate, low, info; category: military, cables, offshore, sar,
    piracy_or_security, drifting_object, wreck, aids_to_navigation, ice, survey...; topic: a feed slug (ice,
    military...); include_archived needs a paid plan. Returns count and compact warnings."""
    data = _get("/api/v2/messages/", {
        "navarea_id": navarea_id, "coastal_id": coastal_id, "country": country, "q": q, "date_from": date_from, "date_to": date_to,
        "ai_severity": severity, "ai_category": category, "ai_in_force": in_force_only or None, "topic": topic,
        "include_archived": include_archived or None, "has_coordinates": has_coordinates, "include_ai_analysis": True,
        "include_coordinates": True, "page": page, "page_size": min(50, max(1, page_size))})
    if "error" in data:
        return json.dumps(data)
    return json.dumps({"count": data.get("count"), "page": data.get("page"), "notes": (data.get("meta") or {}).get("warnings"),
                       "warnings": [_compact(w) for w in data.get("results") or []]}, ensure_ascii=False)


@mcp.tool()
def warnings_near(lat: float, lon: float, radius_nm: float = 30) -> str:
    """Warnings in force within radius_nm (up to 200) of a position, with distance and bearing to the nearest point."""
    data = _get("/api/v2/near/", {"lat": lat, "lon": lon, "radius_nm": min(200.0, max(1.0, radius_nm))})
    return json.dumps(data, ensure_ascii=False)[:60000]


@mcp.tool()
def route_check(waypoints: list[list[float]], speed_kn: float = 12, corridor_nm: float = 10, departure: str | None = None) -> str:
    """A voyage: waypoints as [[lat, lon], ...] (two or more), speed in knots, corridor in NM, departure ISO UTC
    (default now). Returns the route length, the NAVAREAs crossed in order and every warning within the corridor
    with its distance along the route and whether it is in force at the ETA of that point."""
    body = {"waypoints": [{"lat": p[0], "lon": p[1]} for p in waypoints], "speed_kn": speed_kn, "corridor_nm": corridor_nm}
    if departure:
        body["departure"] = departure
    r = requests.post(f"{BASE}/api/v2/route/", json=body, headers=HEADERS, timeout=120)
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        data = {"error": r.status_code, "detail": r.text[:200]}
    if r.status_code >= 400:
        return json.dumps({"error": r.status_code, **(data if isinstance(data, dict) else {})})
    for item in data.get("results") or []:
        item.pop("ai", None) if not isinstance(item.get("ai"), dict) else None
    return json.dumps(data, ensure_ascii=False)[:80000]


@mcp.tool()
def navareas() -> str:
    """The 21 NAVAREAs: id (I..XXI), coordinator, the region id to use as navarea_id, warnings in force."""
    data = _get("/api/v2/navarea-zones/")
    if "error" in data:
        return json.dumps(data)
    rows = []
    for f in data.get("features") or []:
        p = f.get("properties") or {}
        rows.append({k: p.get(k) for k in ("id", "name", "coordinator", "navarea_id", "in_force")})
    return json.dumps(rows, ensure_ascii=False)


@mcp.tool()
def feeds() -> str:
    """Every themed feed (military, cables, offshore, ice...) with its endpoint and how many of its warnings are in force."""
    return json.dumps(_get("/api/v2/feeds/"), ensure_ascii=False)[:40000]


@mcp.tool()
def my_vessels() -> str:
    """The vessels and voyages of the key's account (SeaLagom Noon): names, IMO, voyages with status, last report."""
    return json.dumps(_get("/api/map/vessels/"), ensure_ascii=False)[:40000]


@mcp.tool()
def post_noon_report(voyage_public_id: str, lat: float, lon: float, values: dict, kind: str = "noon",
                     reported_at: str | None = None, confirm: bool = False) -> str:
    """Post a report to a voyage: position, the figures in values (keys from the vessel's report form:
    speed, distance, rpm, fuel...), kind (noon, departure, arrival, position...), reported_at ISO UTC.
    A 409 answer lists checks; confirm=true saves anyway."""
    body = {"kind": kind, "lat": lat, "lon": lon, "values": values, "confirm": confirm}
    if reported_at:
        body["reported_at"] = reported_at
    r = requests.post(f"{BASE}/api/map/voyages/{voyage_public_id}/reports/", json=body, headers=HEADERS, timeout=60)
    return r.text[:20000]


@mcp.tool()
def weather_at(lat: float, lon: float, time: str | None = None) -> str:
    """Wind, sea state and the forecast at a position and time (ISO UTC, default now)."""
    return json.dumps(_get("/api/map/weather/", {"lat": lat, "lon": lon, "time": time}), ensure_ascii=False)[:20000]


@mcp.tool()
def find_port(q: str, lat: float | None = None, lon: float | None = None, top: bool = False) -> str:
    """Ports by name, UN/LOCODE or country, or the nearest to a position (lat, lon). Each row has slug, name,
    country, UN/LOCODE, position, harbour size, NAVAREA. Use the slug with port_details."""
    params: dict[str, Any] = {"q": q, "lat": lat, "lon": lon, "page_size": 20}
    if top:
        params.update({"sort": "rank", "top": 1})
    d = _get("/api/v2/ports/", params)
    if isinstance(d, dict) and "ports" in d:
        keys = ("slug", "name", "country_code", "un_locode", "lat_decimal", "lon_decimal", "harbor_size", "navarea_roman", "distance_nm")
        d = {"total": d.get("total_count"), "ports": [{k: p.get(k) for k in keys if p.get(k) is not None} for p in d["ports"]]}
    return json.dumps(d, ensure_ascii=False)[:30000]


@mcp.tool()
def port_details(slug: str) -> str:
    """One port by slug: time zone and DST, tide range, depths, max draft, harbour size and type, shelter,
    approach and pilotage, VTS and VHF channels, anchorages, restrictions, facilities (terminals, bunkers,
    water, repairs), the warnings in force near it and the routes shared through it."""
    d = _get(f"/api/v2/ports/{slug}/")
    if isinstance(d, dict) and "port" in d:
        port = d["port"]
        port.pop("images", None)
        d = {"port": port, "warnings_near": (d.get("warning_messages") or [])[:30], "routes": d.get("routes"), "resources": d.get("attached_resources")}
    return json.dumps(d, ensure_ascii=False, default=str)[:40000]


@mcp.tool()
def stations_near(lat: float, lon: float, radius_nm: float = 200) -> str:
    """Rescue coordination centres covering a position and the DSC coast stations in range (NGA Pub 117):
    MMSI, bands and frequencies, watch times, telephone, e-mail."""
    return json.dumps(_get("/api/v2/stations/near/", {"lat": lat, "lon": lon, "radius_nm": radius_nm}), ensure_ascii=False)[:30000]


@mcp.tool()
def find_vessel(q: str) -> str:
    """A vessel by name, call sign or MMSI: every warning that names it (region, number, in force, link),
    the vessel rows (name, MMSI, call sign, how many warnings), coast stations with that MMSI, and the
    last AIS report when the live feed is on (ais_live says). The warning text is the authority."""
    return json.dumps(_get("/api/v2/vessels/", {"q": q, "limit": 30}), ensure_ascii=False)[:40000]


@mcp.tool()
def convert_route(waypoints: list[list[float]], to: str = "rtz", name: str = "Route") -> str:
    """Write a route as a file: to = rtz (ECDIS, IEC 61174), gpx, kml (Google Earth, My Maps), csv or nmea.
    waypoints [[lat, lon], ...]. Returns the file text; save it with the matching extension."""
    body = {"waypoints": [{"lat": p[0], "lon": p[1]} for p in waypoints], "name": name}
    r = requests.post(f"{BASE}/api/v2/route/convert/", params={"to": to}, json=body, headers=HEADERS, timeout=60)
    return r.text[:200000]


@mcp.tool()
def rigs() -> str:
    """Mobile offshore drilling units with their last reported positions (from the warnings)."""
    return json.dumps(_get("/api/v2/rigs/"), ensure_ascii=False, default=str)[:40000]


if __name__ == "__main__":
    if not KEY:
        print("Set SEALAGOM_API_KEY (a key from https://www.sealagom.com/profile/?tab=api); the open tools still work without it.")
    mcp.run()
