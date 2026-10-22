/**
 * SeaLagom API client for Node 18+, Deno, Bun and browsers (fetch). No dependencies.
 *
 *   import { SeaLagom } from "./sealagom.mjs";
 *   const api = new SeaLagom("YOUR_KEY");
 *   const page = await api.messages({ navarea_id: 1, ai_in_force: true });
 *   for await (const w of api.each("/api/v2/messages/", { navarea_id: 1 })) { ... }
 *   const check = await api.routeFile(fileOrBlob, { corridor_nm: 15 });
 *
 * Lists are arrays: { ai_severity: ["critical", "high"] }. Errors throw SeaLagomError {status, detail}.
 */

export const BASE = "https://www.sealagom.com";

export class SeaLagomError extends Error {
  constructor(status, detail) {
    super(`${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

export class SeaLagom {
  constructor(key, { base = BASE, fetchImpl } = {}) {
    this.key = (key || (typeof process !== "undefined" ? process.env?.SEALAGOM_API_KEY : "") || "").trim();
    if (!this.key) throw new Error("Pass the key or set SEALAGOM_API_KEY. Get one at https://www.sealagom.com/profile/?tab=api");
    this.base = base.replace(/\/$/, "");
    this.fetch = fetchImpl || globalThis.fetch.bind(globalThis);
    this.lastHeaders = {};
  }

  query(params = {}) {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null) continue;
      if (Array.isArray(v)) v.forEach((x) => q.append(k, String(x)));
      else if (typeof v === "boolean") q.append(k, v ? "true" : "false");
      else q.append(k, String(v));
    }
    const s = q.toString();
    return s ? `?${s}` : "";
  }

  async request(path, { method = "GET", params, json, form } = {}) {
    const headers = { "X-API-Token": this.key, Accept: "application/json" };
    let body;
    if (json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(json);
    } else if (form) {
      body = form; // FormData: the browser or Node sets the multipart boundary
    }
    const r = await this.fetch(`${this.base}${path}${this.query(params)}`, { method, headers, body });
    this.lastHeaders = Object.fromEntries(r.headers.entries());
    if (!r.ok) {
      let detail = "";
      try {
        detail = (await r.json()).detail || "";
      } catch {
        detail = (await r.text().catch(() => "")).slice(0, 200);
      }
      throw new SeaLagomError(r.status, detail || r.statusText);
    }
    return r.json();
  }

  /** One page. */
  messages(params) {
    return this.request("/api/v2/messages/", { params });
  }
  navareas(params) {
    return this.request("/api/v2/navarea/", { params });
  }
  coastals(params) {
    return this.request("/api/v2/coastal/", { params });
  }
  region(scope, id, params) {
    return this.request(`/api/v2/${scope}/${Number(id)}/`, { params });
  }
  ice(params) {
    return this.request("/api/v2/ice/", { params });
  }
  feed(slug, params) {
    return this.request(`/api/v2/feeds/${encodeURIComponent(slug)}/`, { params });
  }
  feeds() {
    return this.request("/api/v2/feeds/");
  }

  /** Every result of every page, lazily. */
  async *each(path, params = {}) {
    let page = 1;
    for (;;) {
      const data = await this.request(path, { params: { ...params, page } });
      for (const row of data.results || []) yield row;
      if (!data.next) return;
      page += 1;
    }
  }

  /** POST /api/v2/route/ with waypoints [[lat, lon], ...] or [{lat, lon}, ...]. */
  route(waypoints, { speed_kn = 12, corridor_nm = 10, departure } = {}) {
    const wps = waypoints.map((p) => (Array.isArray(p) ? { lat: p[0], lon: p[1] } : p));
    return this.request("/api/v2/route/", { method: "POST", json: { waypoints: wps, speed_kn, corridor_nm, ...(departure ? { departure } : {}) } });
  }

  /** POST /api/v2/route/ with a route file: a File or Blob (browser) or { name, bytes } (Node). */
  routeFile(file, { speed_kn = 12, corridor_nm = 10, departure } = {}) {
    const form = new FormData();
    if (file instanceof Blob) form.append("file", file, file.name || "route");
    else form.append("file", new Blob([file.bytes]), file.name || "route");
    form.append("speed_kn", String(speed_kn));
    form.append("corridor_nm", String(corridor_nm));
    if (departure) form.append("departure", departure);
    return this.request("/api/v2/route/", { method: "POST", form });
  }

  // -- lookups: ports, stations, vessels and MMSI, rigs, zones, lights, stats ---------------------
  /** Warnings in force near a position, with distance and bearing. */
  near(lat, lon, radius_nm = 30) {
    return this.request("/api/v2/near/", { params: { lat, lon, radius_nm } });
  }
  /** Ports by name, UN/LOCODE or country, or the nearest to { lat, lon }; top: the main ports first. */
  ports(q = "", { lat, lon, top = false, page = 1, page_size = 40 } = {}) {
    return this.request("/api/v2/ports/", { params: { q: q || undefined, lat, lon, page, page_size, ...(top ? { sort: "rank", top: 1 } : {}) } });
  }
  /** One port: time zone, depths, approach and pilotage, VTS, anchorages, restrictions, facilities, warnings, routes. */
  port(slug) {
    return this.request(`/api/v2/ports/${encodeURIComponent(slug)}/`);
  }
  portDistance(fromSlug, toSlug) {
    return this.request("/api/v2/port-distances/", { params: { from: fromSlug, to: toSlug } });
  }
  /** Every rescue centre and DSC coast station (NGA Pub 117), with MMSI. */
  stations() {
    return this.request("/api/v2/stations/");
  }
  stationsNear(lat, lon, radius_nm = 200, limit = 12) {
    return this.request("/api/v2/stations/near/", { params: { lat, lon, radius_nm, limit } });
  }
  station(id) {
    return this.request(`/api/v2/stations/${Number(id)}/`);
  }
  /** A vessel by name, call sign or MMSI: the warnings naming it, its rows (name, MMSI, call sign), stations with that MMSI, live AIS when on. */
  vessels(q, limit = 50) {
    return this.request("/api/v2/vessels/", { params: { q, limit } });
  }
  vessel(mmsi, limit = 50) {
    return this.request(`/api/v2/vessels/${encodeURIComponent(String(mmsi))}/`, { params: { limit } });
  }
  rigs() {
    return this.request("/api/v2/rigs/");
  }
  zones() {
    return this.request("/api/v2/zones/");
  }
  navareaZones() {
    return this.request("/api/v2/navarea-zones/");
  }
  lights({ scope, region_id, country } = {}) {
    return this.request("/api/v2/lights/", { params: { scope, region_id, country } });
  }
  stats() {
    return this.request("/api/v2/stats/");
  }

  // -- route converter: any route in, RTZ, GPX, KML, CSV or NMEA out (the file as text) ------------
  async convertRoute(waypoints, to = "rtz", name = "") {
    const wps = waypoints.map((p) => (Array.isArray(p) ? { lat: p[0], lon: p[1] } : p));
    return this.requestText(`/api/v2/route/convert/?to=${encodeURIComponent(to)}`, { method: "POST", json: { waypoints: wps, name } });
  }
  async convertRouteFile(file, to = "rtz") {
    const form = new FormData();
    if (file instanceof Blob) form.append("file", file, file.name || "route");
    else form.append("file", new Blob([file.bytes]), file.name || "route");
    return this.requestText(`/api/v2/route/convert/?to=${encodeURIComponent(to)}`, { method: "POST", form });
  }
  async requestText(path, { method = "GET", json, form } = {}) {
    const headers = { "X-API-Token": this.key };
    let body;
    if (json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(json);
    } else if (form) body = form;
    const r = await this.fetch(`${this.base}${path}`, { method, headers, body });
    this.lastHeaders = Object.fromEntries(r.headers.entries());
    if (!r.ok) throw new SeaLagomError(r.status, (await r.text().catch(() => "")).slice(0, 200) || r.statusText);
    return r.text();
  }
}
