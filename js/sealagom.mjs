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

  navareaZones() {
    return this.request("/api/public/navarea-zones/");
  }
  stationsNear(lat, lon, radius_nm = 200, limit = 12) {
    return this.request("/api/public/coast-stations/near/", { params: { lat, lon, radius_nm, limit } });
  }
}
