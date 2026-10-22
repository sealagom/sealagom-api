"""SeaLagom API client, Python 3.9+, one dependency (requests).

    from sealagom import SeaLagom
    api = SeaLagom("YOUR_KEY")
    page = api.messages(navarea_id=1, ai_in_force=True)        # one page (dict)
    for w in api.messages(navarea_id=1, ai_in_force=True):     # every page, lazily
        ...
    api.route_file("passage.rtz", corridor_nm=15)              # the NAVAREAs crossed and the warnings along
    api.route([(51.0, 1.5), (36.1, -5.4)], speed_kn=14)

Lists are passed as Python lists: api.messages(ai_severity=["critical", "high"]).
Every answer is the JSON as served; the HTTP headers X-API-Tokens-Used / -Remaining are on
api.last_headers. Errors raise SeaLagomError with the status and the server's detail.
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import requests

BASE = "https://www.sealagom.com"
USER_AGENT = "sealagom-python/1.0"


class SeaLagomError(RuntimeError):
    def __init__(self, status: int, detail: str):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


class Page(dict):
    """A page of results that also iterates over every following page."""

    def __init__(self, data: dict, api: "SeaLagom", path: str, params: dict):
        super().__init__(data)
        self._api, self._path, self._params = api, path, params

    def __iter__(self) -> Iterator[dict]:  # type: ignore[override]
        page = self
        while True:
            for row in page.get("results") or []:
                yield row
            if not page.get("next"):
                return
            nxt = dict(self._params)
            nxt["page"] = int(page.get("page") or 1) + 1
            page = self._api._get(self._path, nxt)


class SeaLagom:
    def __init__(self, key: str | None = None, base: str = BASE, timeout: float = 60.0):
        self.key = (key or os.environ.get("SEALAGOM_API_KEY") or "").strip()
        if not self.key:
            raise ValueError("Pass the key or set SEALAGOM_API_KEY. Get one at https://www.sealagom.com/profile/?tab=api")
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.last_headers: dict[str, str] = {}
        self._s = requests.Session()
        self._s.headers.update({"X-API-Token": self.key, "User-Agent": USER_AGENT, "Accept": "application/json"})

    # -- plumbing -------------------------------------------------------------------------------
    @staticmethod
    def _clean(params: dict) -> list[tuple[str, Any]]:
        out: list[tuple[str, Any]] = []
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                out.append((k, "true" if v else "false"))
            elif isinstance(v, (list, tuple, set)):
                out.extend((k, str(x)) for x in v)
            else:
                out.append((k, str(v)))
        return out

    def _raise(self, r: requests.Response) -> None:
        if r.status_code < 400:
            return
        try:
            detail = r.json().get("detail") or r.text[:200]
        except Exception:  # noqa: BLE001
            detail = r.text[:200]
        raise SeaLagomError(r.status_code, detail)

    def _get(self, path: str, params: dict) -> Page:
        r = self._s.get(f"{self.base}{path}", params=self._clean(params), timeout=self.timeout)
        self.last_headers = dict(r.headers)
        self._raise(r)
        return Page(r.json(), self, path, params)

    # -- warnings -------------------------------------------------------------------------------
    def messages(self, **params) -> Page:
        """GET /api/v2/messages/: navarea_id, coastal_id, country, q, date_from, date_to, keyword,
        has_coordinates, include_archived, include_ai_analysis, include_geo_features, ai_severity,
        ai_category, ai_in_force, expires_within_hours, exclude_routine, topic, page, page_size..."""
        return self._get("/api/v2/messages/", params)

    def navareas(self, **params) -> Page:
        return self._get("/api/v2/navarea/", params)

    def coastals(self, **params) -> Page:
        return self._get("/api/v2/coastal/", params)

    def region(self, scope: str, region_id: int, **params) -> dict:
        return dict(self._get(f"/api/v2/{scope}/{int(region_id)}/", params))

    def ice(self, **params) -> Page:
        return self._get("/api/v2/ice/", params)

    def feed(self, slug: str, **params) -> Page:
        return self._get(f"/api/v2/feeds/{slug}/", params)

    def feeds(self) -> dict:
        return dict(self._get("/api/v2/feeds/", {}))

    # -- route ----------------------------------------------------------------------------------
    def route(self, waypoints: list[tuple[float, float]], *, speed_kn: float = 12, corridor_nm: float = 10, departure: str | None = None) -> dict:
        """POST /api/v2/route/ with JSON waypoints [(lat, lon), ...]."""
        body: dict[str, Any] = {"waypoints": [{"lat": la, "lon": lo} for la, lo in waypoints], "speed_kn": speed_kn, "corridor_nm": corridor_nm}
        if departure:
            body["departure"] = departure
        r = self._s.post(f"{self.base}/api/v2/route/", json=body, timeout=self.timeout)
        self.last_headers = dict(r.headers)
        self._raise(r)
        return r.json()

    def route_file(self, path: str, *, speed_kn: float = 12, corridor_nm: float = 10, departure: str | None = None) -> dict:
        """POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA)."""
        data = {"speed_kn": str(speed_kn), "corridor_nm": str(corridor_nm)}
        if departure:
            data["departure"] = departure
        with open(path, "rb") as fh:
            r = self._s.post(f"{self.base}/api/v2/route/", data=data, files={"file": (os.path.basename(path), fh)}, timeout=self.timeout)
        self.last_headers = dict(r.headers)
        self._raise(r)
        return r.json()

    # -- noon reports, vessels, voyages (the key signs in on /api/map/) -------------------------------
    def _post(self, path: str, body: dict) -> dict:
        r = self._s.post(f"{self.base}{path}", json=body, timeout=self.timeout)
        self.last_headers = dict(r.headers)
        if r.status_code == 409:
            return r.json()  # figures to check: send confirm=True to save anyway
        self._raise(r)
        return r.json()

    def account(self) -> dict:
        return dict(self._get("/api/map/account/", {}))

    def vessels(self) -> list[dict]:
        return list(self._get("/api/map/vessels/", {}).get("vessels") or [])

    def add_vessel(self, name: str, **fields) -> dict:
        """imo, mmsi, call_sign, flag, vessel_type, fleet."""
        return self._post("/api/map/vessels/", {"name": name, **fields})

    def voyages(self, vessel_public_id: str) -> list[dict]:
        return list(self._get(f"/api/map/vessels/{vessel_public_id}/voyages/", {}).get("voyages") or [])

    def open_voyage(self, vessel_public_id: str, **fields) -> dict:
        """number, name, departure_name, arrival_name, charterer, etd, eta, waypoints=[{lat, lon}]."""
        return self._post(f"/api/map/vessels/{vessel_public_id}/voyages/", fields)

    def voyage(self, public_id: str) -> dict:
        return dict(self._get(f"/api/map/voyages/{public_id}/", {}))

    def report_form(self, voyage_public_id: str) -> dict:
        """The report items (keys, labels, units) the vessel expects in `values`."""
        return dict(self._get(f"/api/map/voyages/{voyage_public_id}/report-form/", {}))

    def reports(self, voyage_public_id: str) -> list[dict]:
        return list(self._get(f"/api/map/voyages/{voyage_public_id}/reports/", {}).get("reports") or [])

    def post_report(self, voyage_public_id: str, *, lat: float | None = None, lon: float | None = None, values: dict | None = None,
                    kind: str = "noon", reported_at: str | None = None, confirm: bool = False) -> dict:
        """A noon (or other) report from a bridge PC, a GPS logger or a script. 409 answers carry `checks`;
        confirm=True saves anyway."""
        body: dict[str, Any] = {"kind": kind, "values": values or {}, "confirm": confirm}
        if lat is not None and lon is not None:
            body["lat"], body["lon"] = lat, lon
        if reported_at:
            body["reported_at"] = reported_at
        return self._post(f"/api/map/voyages/{voyage_public_id}/reports/", body)

    def weather(self, lat: float, lon: float, time: str | None = None) -> dict:
        """Wind, sea and the forecast at a position and time (UTC ISO; default now)."""
        return dict(self._get("/api/map/weather/", {"lat": lat, "lon": lon, "time": time}))

    def weather_track(self, voyage_public_id: str) -> dict:
        return dict(self._get(f"/api/map/voyages/{voyage_public_id}/weather-track/", {}))

    # -- open endpoints (no key needed, but the key does no harm) -----------------------------------
    def navarea_zones(self) -> dict:
        return dict(self._get("/api/public/navarea-zones/", {}))

    def stations_near(self, lat: float, lon: float, radius_nm: float = 200, limit: int = 12) -> dict:
        return dict(self._get("/api/public/coast-stations/near/", {"lat": lat, "lon": lon, "radius_nm": radius_nm, "limit": limit}))


if __name__ == "__main__":  # a smoke test: python sealagom.py
    api = SeaLagom()
    page = api.messages(ai_in_force=True, page_size=5)
    print(page["count"], "warnings in force;", api.last_headers.get("X-API-Tokens-Remaining"), "requests left")
    for w in page["results"]:
        print(" ", w.get("region_title"), w.get("number"), (w.get("content_en") or w.get("content") or "")[:70].replace("\n", " "))
