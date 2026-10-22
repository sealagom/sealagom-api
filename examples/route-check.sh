#!/usr/bin/env sh
# Send a route file, get the NAVAREAs and the warnings along it. Any shell with curl; jq optional.
#   SEALAGOM_API_KEY=YOUR_KEY ./route-check.sh passage.rtz 15
ROUTE="${1:-passage.rtz}"; CORRIDOR="${2:-10}"
curl -sS -X POST https://www.sealagom.com/api/v2/route/ -H "X-API-Token: $SEALAGOM_API_KEY" \
  -F "file=@$ROUTE" -F "corridor_nm=$CORRIDOR" -o result.json || exit 1
if command -v jq >/dev/null 2>&1; then
  jq -r '"\(.route_nm) NM, NAVAREAs: \([.navareas[].name] | join(", ")), \(.count) warnings on the route",
         (.results[] | "  \(.region_title) \(.number)  \(.distance_nm) NM off at \(.along_nm) NM  \(.verdict)  \(.ai.headline // "")")' result.json
else
  cat result.json
fi
