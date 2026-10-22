# SeaLagom API

Navigational warnings of the whole world, as issued by the NAVAREA coordinators and the coastal
authorities, with positions, shapes and an analysis of every warning. One key, one base URL:

```
https://www.sealagom.com/api/v2/
X-API-Token: YOUR_KEY
```

This repository is the integration kit: the OpenAPI spec, the data models, small clients for
Python and JavaScript, an MCP server so Claude, Cursor, VS Code, Windsurf and any other agent can
use the data as tools, and a GitHub Action that checks a route against the warnings in force.

## Get a key

| Way | Where |
|---|---|
| Sign in with GitHub, key in ten seconds | https://www.sealagom.com/login/ |
| Account and key by hand | https://www.sealagom.com/profile/?tab=api |
| From a script or an agent, paid in crypto | `POST https://www.sealagom.com/api/agent/checkout/` (see section 14 of the README below) |

Free keys get the Developer allowance on active warnings. Archived warnings, the analysis object,
geo features, feeds and the route check with full detail come with the paid plans:
https://www.sealagom.com/api/docs/#subscription-plans

## Quick start

```bash
# Warnings in force in NAVAREA I that mention a position, with the analysis
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&has_coordinates=true&include_ai_analysis=true" \
  -H "X-API-Token: YOUR_KEY"

# Send a route, get the NAVAREAs it crosses and every warning within 15 NM of it
curl -X POST https://www.sealagom.com/api/v2/route/ -H "X-API-Token: YOUR_KEY" \
  -F "file=@passage.rtz" -F "corridor_nm=15"

# The same from a tool that can only drop a file: the key in the address
curl -X POST https://www.sealagom.com/api/v2/drop/YOUR_KEY/route/ -F "file=@passage.gpx"
```

Python:

```python
from sealagom import SeaLagom

api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True, include_ai_analysis=True):
    print(w["number"], w["ai_analysis"]["headline"] if w.get("ai_analysis") else w["content"][:80])

check = api.route_file("passage.rtz", corridor_nm=15)
print(check["route_nm"], [z["name"] for z in check["navareas"]], check["count"], "warnings on the route")
```

JavaScript (Node 18+, Deno, Bun, browsers):

```js
import { SeaLagom } from "./js/sealagom.mjs";

const api = new SeaLagom("YOUR_KEY");
const page = await api.messages({ navarea_id: 1, ai_in_force: true });
console.log(page.count, page.results[0]?.number);
```

## Agents and editors (MCP)

`mcp/sealagom_mcp.py` is an MCP server with the tools `search_warnings`, `warnings_near`,
`route_check`, `navareas` and `feeds`. Claude Desktop, Claude Code, Cursor, VS Code (Copilot agent
mode), Windsurf and Zed all speak MCP; the config snippets are in [mcp/README.md](mcp/README.md).
Two lines:

```bash
pip install "mcp[cli]" requests
SEALAGOM_API_KEY=YOUR_KEY python mcp/sealagom_mcp.py
```

No MCP? Give the agent the README the API itself serves, it is written for them:
https://www.sealagom.com/api/public/api-setup-readme/

## Any system: drop a route, get the result

The same call from whatever you have: [examples/route-check.bat](examples/route-check.bat)
(Windows batch), [examples/route-check.ps1](examples/route-check.ps1) (PowerShell),
[examples/route-check.sh](examples/route-check.sh) (any shell), the Python and JavaScript clients
above, or the drop link with the key in the address for tools that can only POST a file:

```
POST https://www.sealagom.com/api/v2/drop/YOUR_KEY/route/    form field "file"
```

## Pay from the console

No browser needed: [examples/pay-from-console.sh](examples/pay-from-console.sh) opens a crypto
invoice for an API plan and the status link returns the key once the coins arrived
(`POST /api/agent/checkout/`, then `GET` the `status_url`). Donations of any size:
`POST /api/agent/donate/ {"amount": 0.20}`.

## GitHub Action: check a route in CI

Put a route file in a repository and let the Action fail the build when a warning of the chosen
severity lies on the route. See [examples/route-check.yml](examples/route-check.yml).

## What is in the data

| Object | Schema | Notes |
|---|---|---|
| Warning | [models/warning.schema.json](models/warning.schema.json) | number, region, text (original and English), positions, geo features, analysis |
| Analysis | [models/analysis.schema.json](models/analysis.schema.json) | headline, summary, category, severity, live status, validity, hazards, keep-clear distance, contacts, vessels |
| Route result | [models/route-result.schema.json](models/route-result.schema.json) | route length, NAVAREAs crossed, warnings along the route with distance and ETA verdict |

The full specification: [openapi.yaml](openapi.yaml). Endpoints without a key: the 21 NAVAREA
zones as GeoJSON, coast radio and rescue stations near a position, port distances, the feed
catalogue, and free RSS and plain-text feeds of the newest warnings.

## Rules of the data

The warnings are the authority. SeaLagom supports the official broadcast and never replaces it;
the analysis is machine-made and can be wrong, the original text is the authoritative one. Keep
the key and the drop link secret. Credit "SeaLagom, www.sealagom.com" where the data is shown.

Contact: contact@sealagom.com
