/* SeaLagom API client for C. One dependency: libcurl (apt install libcurl4-openssl-dev, brew install curl).
 * MIT License, Copyright (c) 2026 SeaLagom. See LICENSE in the repository root.
 *
 *   sealagom_result r;
 *   if (sealagom_warnings_near(NULL, 55.0, 3.0, 60, &r) == 0) puts(r.body);   /* key NULL: SEALAGOM_API_KEY */
 *   else fprintf(stderr, "SeaLagom %d: %s\n", r.status, r.detail);
 *   sealagom_free(&r);
 *
 *   gcc -o near examples/c/near.c c/sealagom.c -lcurl
 *
 * Every call returns 0 when the server answered 2xx or 3xx and r.body holds the JSON as served (yours to
 * parse: cJSON, jansson, or the helpers in examples/c/near.c for a quick look). On an HTTP error the return
 * value is the status (401 no or wrong key, 403 the plan does not include the call, 429 allowance or rate
 * limit reached) and r.detail holds the server's message; on a transport error it is -1 and r.detail holds
 * the curl message. Timeout 60 s. Call sealagom_free on every result, success or not.
 * Without a key only the public endpoints answer (feeds, the NAVAREA zones, stations near a position).
 */
#ifndef SEALAGOM_H
#define SEALAGOM_H

#include <stddef.h>

#define SEALAGOM_BASE "https://www.sealagom.com"
#define SEALAGOM_USER_AGENT "sealagom-c/1.0"

typedef struct {
    int status;         /* HTTP status, 0 on a transport error */
    char *body;         /* the answer as served (malloc), NUL terminated; NULL on a transport error */
    size_t body_len;
    char detail[256];   /* the server's "detail" or the curl message when the call failed */
    long tokens_remaining; /* X-API-Tokens-Remaining, -1 when the header was absent */
} sealagom_result;

/* Any GET under the base URL, e.g. "/api/v2/feeds/" or "/api/v2/navarea/". */
int sealagom_get(const char *key, const char *path_and_query, sealagom_result *out);

/* GET /api/v2/messages/?<query>. query: "navarea_id=1&ai_in_force=true&page_size=20" (URL encoded), or NULL.
 * Answer: count, next, results[]. */
int sealagom_search_warnings(const char *key, const char *query, sealagom_result *out);

/* GET /api/v2/near/: warnings in force within radius_nm (up to 200) of a position. Answer: count, warnings[]
 * with region_title, number, distance_nm, nearest [lat, lon], ai (headline, severity, valid_until). */
int sealagom_warnings_near(const char *key, double lat, double lon, double radius_nm, sealagom_result *out);

/* POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA; up to 5 MB). departure ISO UTC or
 * NULL. Answer: route_nm, navareas[], count, results[] with distance_nm, along_nm, verdict, ai. */
int sealagom_route_check_file(const char *key, const char *path, double speed_kn, double corridor_nm,
                              const char *departure, sealagom_result *out);

/* GET /api/v2/navarea/ and GET /api/v2/feeds/ (feeds needs no key). */
int sealagom_navareas(const char *key, sealagom_result *out);
int sealagom_feeds(const char *key, sealagom_result *out);

void sealagom_free(sealagom_result *r);

#endif
