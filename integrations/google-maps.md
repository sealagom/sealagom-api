# Google Earth, Google My Maps, Google Maps

Google Earth opens KML and KMZ; Google My Maps imports KML, CSV, GPX and XLSX as a layer; Google
Maps shows a My Maps layer. Three ways to put SeaLagom data there.

## A route as KML

The converter writes KML from any route file (RTZ, RT3, GPX, KML, CSV, NMEA) or from waypoints:

```bash
curl -X POST "https://www.sealagom.com/api/v2/route/convert/?to=kml" -H "X-API-Token: YOUR_KEY" -F file=@passage.rtz -o passage.kml
```

Open `passage.kml` in Google Earth, or My Maps, Import, choose the file. The waypoints come as
placemarks and the route as a line. The same converter runs in the browser or in Node without the
API: `js/route-convert.mjs` in the tools library (https://www.sealagom.com/github/tools/).

## The warnings in force as KML

The warnings carry their positions. Twenty lines write a KML with one placemark per position:

```python
from xml.sax.saxutils import escape
import sealagom  # python/sealagom.py from this kit

api = sealagom.SeaLagom("YOUR_KEY")
page = api.messages(navarea_id=1, ai_in_force=True, include_coordinates=True, include_ai_analysis=True, page_size=100)
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>NAVAREA I in force</name>']
for w in page["results"]:
    ai = w.get("ai_analysis") or {}
    title = f'{w["region_title"]} {w["number"]}' + (f' - {ai["headline"]}' if ai.get("headline") else "")
    text = (w.get("content_en") or w.get("content") or "")[:1500]
    for pos in w.get("coordinates") or []:
        lat, lon = (pos.get("lat"), pos.get("lon")) if isinstance(pos, dict) else (pos[0], pos[1])
        out.append(f"<Placemark><name>{escape(title)}</name><description>{escape(text)}</description>"
                   f"<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>")
out.append("</Document></kml>")
open("navarea1.kml", "w", encoding="utf-8").write("\n".join(out))
```

Import `navarea1.kml` into My Maps (a layer per NAVAREA or per feed works well) or open it in Google
Earth. Poll and rewrite every 10 to 15 minutes if the layer should stay current.

## The NAVAREA limits

`GET /api/v2/navarea-zones/` is a GeoJSON FeatureCollection of the 21 NAVAREAs (WMO-No. 558 limits).
Google Earth Pro and most GIS tools open GeoJSON as it is; for My Maps convert it to KML first
(`ogr2ogr -f KML navareas.kml navareas.geojson`, or any online converter).

## Positions in a Google Maps link

Any warning position opens in Google Maps as `https://www.google.com/maps?q=LAT,LON`; the vessel and
port lookups (`/api/v2/vessels/`, `/api/v2/ports/<slug>/`) carry decimal positions you can put there.

Credit SeaLagom, www.sealagom.com, on the layer. The warning text is the authority; the analysis
fields can be wrong.
