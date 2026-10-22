/**
 * SeaLagom in Google Sheets and Google Docs (Apps Script).
 *
 * Sheets: Extensions > Apps Script, paste this file, then File > Project settings > Script properties:
 * add SEALAGOM_API_KEY with a key from https://www.sealagom.com/profile/?tab=api (or sign in with GitHub).
 * Formulas:
 *   =SEALAGOM_WARNINGS(1)                    warnings in force in NAVAREA I (region id), newest first
 *   =SEALAGOM_WARNINGS(1, 20, "critical")    the 20 newest with severity critical (Full API for the analysis columns)
 *   =SEALAGOM_NEAR(36.1, -5.4, 30)           warnings within 30 NM of a position
 *   =SEALAGOM_PORT("gibraltar")              one port as label/value rows: time zone, pilotage, VTS, anchorages, facilities
 *   =SEALAGOM_STATIONS(36.1, -5.4, 150)      the MRCC covering a position and the DSC stations in range
 *   =SEALAGOM_VESSEL("al dasma")             every warning naming a vessel (name, call sign or MMSI)
 *   =SEALAGOM_ROUTE(A2:B9, 14)               a route from lat/lon cells: distance, NAVAREAs crossed, warnings on it
 * Docs: the menu "SeaLagom" inserts the warnings in force for a NAVAREA at the cursor.
 *
 * Every call is one request against the plan of the key. Credit SeaLagom, www.sealagom.com, where the data is shown.
 */

var BASE = "https://www.sealagom.com";

function key_() {
  var k = PropertiesService.getScriptProperties().getProperty("SEALAGOM_API_KEY");
  if (!k) throw new Error("Add the script property SEALAGOM_API_KEY (https://www.sealagom.com/profile/?tab=api).");
  return k;
}

function get_(path, params) {
  var q = Object.keys(params || {}).filter(function (k) { return params[k] !== undefined && params[k] !== null && params[k] !== ""; })
    .map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); }).join("&");
  var r = UrlFetchApp.fetch(BASE + path + (q ? "?" + q : ""), { headers: { "X-API-Token": key_(), Accept: "application/json" }, muteHttpExceptions: true });
  var d = JSON.parse(r.getContentText());
  if (r.getResponseCode() >= 400) {
    var up = d.upgrade || (d.meta && d.meta.upgrade);
    throw new Error((d.detail || "Refused") + (up ? " Plan " + up.plan + ", " + up.monthly_usd + " USD a month: " + up.plans : ""));
  }
  return d;
}

function post_(path, body) {
  var r = UrlFetchApp.fetch(BASE + path, { method: "post", contentType: "application/json", payload: JSON.stringify(body),
    headers: { "X-API-Token": key_(), Accept: "application/json" }, muteHttpExceptions: true });
  var d = JSON.parse(r.getContentText());
  if (r.getResponseCode() >= 400) throw new Error(d.detail || "Refused");
  return d;
}

function rows_(warnings) {
  var out = [["Region", "Number", "Added", "Headline", "Severity", "Status", "Valid until", "Text", "Link"]];
  warnings.forEach(function (w) {
    var ai = w.ai_analysis || w;
    out.push([w.region_title || w.region || "", w.number || "", w.added_on || "", ai.headline || "", ai.severity || "", ai.status || "",
      ai.valid_until || "", String(w.content_en || w.content || w.text || "").slice(0, 2000),
      w.url || (w.scope ? BASE + "/" + w.scope + "/" + w.region_id + "/message/" + w.id + "/" : "")]);
  });
  return out;
}

/** Warnings in force in a NAVAREA (region id 1..21). @customfunction */
function SEALAGOM_WARNINGS(navareaId, limit, severity) {
  var d = get_("/api/v2/messages/", { navarea_id: navareaId, ai_in_force: true, include_ai_analysis: true, ai_severity: severity, page_size: limit || 50 });
  return rows_(d.results || []);
}

/** Warnings within radius_nm of a position. @customfunction */
function SEALAGOM_NEAR(lat, lon, radiusNm) {
  var d = get_("/api/v2/near/", { lat: lat, lon: lon, radius_nm: radiusNm || 30 });
  var out = rows_(d.warnings || []);
  out[0].push("Distance NM");
  (d.warnings || []).forEach(function (w, i) { out[i + 1].push(w.distance_nm); });
  return out;
}

/** One port by slug as label/value rows. @customfunction */
function SEALAGOM_PORT(slug) {
  var p = get_("/api/v2/ports/" + encodeURIComponent(slug) + "/").port || {};
  var out = [];
  ["name", "country", "un_locode", "latitude_dm", "longitude_dm", "time_zone", "utc_offset_current", "navarea"].forEach(function (k) {
    if (p[k] !== undefined && p[k] !== null && p[k] !== "") out.push([k, String(p[k])]);
  });
  var fields = p.fields || {};
  Object.keys(fields).forEach(function (k) {
    var v = fields[k];
    if (v && typeof v === "object") v = v.value || v.text || JSON.stringify(v);
    if (v) out.push([k, String(v).slice(0, 5000)]);
  });
  return out.length ? out : [["No port with slug " + slug, ""]];
}

/** The MRCC covering a position and the DSC coast stations in range. @customfunction */
function SEALAGOM_STATIONS(lat, lon, radiusNm) {
  var d = get_("/api/v2/stations/near/", { lat: lat, lon: lon, radius_nm: radiusNm || 200 });
  var out = [["Kind", "Name", "Country", "MMSI", "Distance NM", "Telephone", "E-mail", "Bands"]];
  [].concat(d.rcc_covering || [], d.rcc_near || [], d.dsc_near || []).forEach(function (s) {
    out.push([s.kind || "", s.name || "", s.country || "", s.mmsi || "", s.distance_nm || "", s.telephone || s.phone || "", s.email || "",
      (s.bands || []).map(function (b) { return b.band || b; }).join(", ")]);
  });
  return out;
}

/** Every warning naming a vessel (name, call sign or MMSI). @customfunction */
function SEALAGOM_VESSEL(q) {
  var d = get_("/api/v2/vessels/", { q: q, limit: 50 });
  var out = [["Vessel", "MMSI", "Call sign", "Region", "Number", "In force", "Headline", "Link"]];
  (d.warnings || []).forEach(function (w) {
    var v = (w.vessels || [])[0] || {};
    out.push([v.name || "", v.mmsi || "", v.call_sign || "", w.region || "", w.number || "", w.in_force ? "yes" : "no", w.headline || "", w.url || ""]);
  });
  return out;
}

/** A route from a two-column range of lat, lon: length, NAVAREAs crossed, warnings on it. @customfunction */
function SEALAGOM_ROUTE(range, speedKn, corridorNm) {
  var wps = (range || []).filter(function (r) { return r[0] !== "" && r[1] !== ""; }).map(function (r) { return { lat: Number(r[0]), lon: Number(r[1]) }; });
  var d = post_("/api/v2/route/", { waypoints: wps, speed_kn: speedKn || 12, corridor_nm: corridorNm || 10 });
  var out = [["Route NM", d.route_nm], ["NAVAREAs", (d.navareas || []).map(function (z) { return z.name || z.id; }).join(", ")], ["Warnings on the route", d.count]];
  (d.warnings || []).forEach(function (w) { out.push([(w.region || w.region_title || "") + " " + (w.number || ""), (w.headline || String(w.text || "").slice(0, 200)) + (w.url ? " " + w.url : "")]); });
  return out;
}

// ---- Google Docs: a menu that inserts the warnings in force at the cursor -----------------------

function onOpen() {
  try {
    DocumentApp.getUi().createMenu("SeaLagom").addItem("Insert warnings in force for a NAVAREA", "insertWarningsDialog").addToUi();
  } catch (e) { /* not a Doc */ }
}

function insertWarningsDialog() {
  var ui = DocumentApp.getUi();
  var r = ui.prompt("NAVAREA region id (1 to 21)", ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  var d = get_("/api/v2/messages/", { navarea_id: r.getResponseText(), ai_in_force: true, include_ai_analysis: true, page_size: 50 });
  var body = DocumentApp.getActiveDocument().getBody();
  var cursor = DocumentApp.getActiveDocument().getCursor();
  var at = cursor ? body.getChildIndex(cursor.getElement().getParent ? cursor.getElement() : cursor.getElement()) : body.getNumChildren();
  (d.results || []).forEach(function (w, i) {
    var ai = w.ai_analysis || {};
    var line = (w.region_title || "") + " " + (w.number || "") + (ai.headline ? ": " + ai.headline : "") + (ai.severity ? " [" + ai.severity + "]" : "");
    var p = body.insertParagraph(at + i, line);
    p.setLinkUrl(BASE + "/" + w.scope + "/" + w.region_id + "/message/" + w.id + "/");
  });
  body.insertParagraph(at + (d.results || []).length, "Source: SeaLagom, www.sealagom.com. The warning text is the authority.");
}
