# Every feed

One key, `X-API-Token`. Every feed is JSON (`count`, `results[]`, `meta`), and most are also RSS or
plain text with no key. Poll every 10 to 15 minutes. The warning text is the authority; the
analysis fields (headline, severity, validity, keep-clear distance) are machine-made and can be wrong.

## Themed feeds (Full API)

`GET /api/v2/feeds/<slug>/` with the same filters as `/api/v2/messages/` (`navarea_id`, `country`,
`ai_severity`, `expires_within_hours`, `page_size`...). `GET /api/v2/feeds/` lists them with how many
warnings are in force right now.

| Slug | What is in it |
|---|---|
| `military` | Military exercises, firing practice, missile and gunnery areas |
| `security` | Security and restricted areas, piracy and armed robbery notices |
| `space` | Rocket launches, re-entries and space debris fall areas |
| `cables` | Submarine cable and pipeline laying, repair and survey |
| `offshore` | Offshore works, rigs, platforms, wind farms, towing |
| `survey` | Hydrographic, seismic and other survey operations |
| `hazards` | Wrecks, obstructions, drifting containers, buoys and other objects |
| `aton` | Aids to navigation: lights, buoys and beacons out of order, moved or re-established |
| `sar` | Search and rescue: vessels in distress, overdue, persons in the water |
| `ice` | Ice: icebergs, limits, ice edge reports (`/api/v2/ice/`, sorted automatically) |

## Lights and aids out of order

`GET /api/v2/lights/?scope=navarea&region_id=1` (or `?country=`): every aid to navigation reported
unlit, off station, damaged or discontinued, with its condition and the warning it comes from.
`GET /api/v2/stations/` has every rescue centre and DSC coast station with MMSI, bands and watch times.

## By region, country or position (every key)

- `GET /api/v2/messages/?navarea_id=1&ai_in_force=true` the warnings of one NAVAREA (I = 1 ... XXI = 21).
- `GET /api/v2/messages/?country=norway` coastal warnings of a country; `/api/v2/coastal/` lists the regions.
- `GET /api/v2/near/?lat=36.1&lon=-5.4&radius_nm=30` around a position, with distance and bearing.
- `POST /api/v2/route/` along a route (file or waypoints), with the NAVAREAs crossed.
- `GET /api/v2/rigs/` mobile offshore drilling units with their last reported positions.

## RSS and plain text (no key)

- `https://www.sealagom.com/feeds/warnings.xml` the newest 100 warnings; `/feeds/navarea/<id>.xml`, `/feeds/coastal/<id>.xml`.
- `https://www.sealagom.com/feeds/warnings.txt?navarea=1&limit=50` plain text for pagers, spreadsheets (`=IMPORTDATA(...)`), scripts.

## Pushed to you

- Telegram: the SeaLagom bot, `/watch navarea XI critical` sends every new warning of a region to the chat (Contributor).
- X, Facebook, Instagram, Threads, Discord, Slack, Mastodon, Bluesky: [integrations/social.py](integrations/social.py).
- E-mail: the alerts on the site (Profile, Alerts): immediate, daily or weekly, by region and keyword.
- Webhooks for your own system: poll `/api/v2/messages/?ai_in_force=true&page_size=50` and remember the `(scope, region_id, number)` keys you have seen; the loop in [integrations/social.py](integrations/social.py) is the pattern.

## Arithmetic that goes with the data

The free tools library (https://www.sealagom.com/github/tools/) has distances and courses (great circle,
rhumb line), ETA and the speed for an ETA, true and apparent wind, Beaufort, nautical time zones,
positions as DD-MM.MM and back, route files in and out, and a route converter. No key, MIT.
