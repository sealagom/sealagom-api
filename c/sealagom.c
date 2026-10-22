/* SeaLagom API client for C, libcurl. See sealagom.h for the calls.
 * MIT License, Copyright (c) 2026 SeaLagom. See LICENSE in the repository root. */
#include "sealagom.h"

#include <curl/curl.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t on_body(const void *data, size_t size, size_t n, void *userp)
{
    sealagom_result *r = (sealagom_result *)userp;
    size_t add = size * n;
    char *grown = (char *)realloc(r->body, r->body_len + add + 1);
    if (!grown)
        return 0;
    r->body = grown;
    memcpy(r->body + r->body_len, data, add);
    r->body_len += add;
    r->body[r->body_len] = '\0';
    return add;
}

static int starts_with_nocase(const char *line, size_t len, const char *name)
{
    size_t i, n = strlen(name);
    if (len < n)
        return 0;
    for (i = 0; i < n; i++)
        if (tolower((unsigned char)line[i]) != tolower((unsigned char)name[i]))
            return 0;
    return 1;
}

static size_t on_header(const char *line, size_t size, size_t n, void *userp)
{
    sealagom_result *r = (sealagom_result *)userp;
    size_t len = size * n;
    const char *name = "X-API-Tokens-Remaining:";
    if (starts_with_nocase(line, len, name))
        r->tokens_remaining = strtol(line + strlen(name), NULL, 10);
    return len;
}

/* The server's "detail" string out of the error body (\" and \\ unescaped), else the first 200 bytes. */
static void pick_detail(sealagom_result *r)
{
    const char *p = r->body ? strstr(r->body, "\"detail\"") : NULL;
    size_t i = 0;
    if (p && (p = strchr(p + 8, ':')) != NULL && (p = strchr(p, '"')) != NULL) {
        for (p++; *p && *p != '"' && i < sizeof(r->detail) - 1; p++) {
            if (*p == '\\' && p[1])
                p++;
            r->detail[i++] = *p;
        }
        r->detail[i] = '\0';
    } else if (r->body) {
        snprintf(r->detail, sizeof(r->detail), "%.200s", r->body);
    }
}

static void add_field(curl_mime *form, const char *name, const char *value)
{
    curl_mimepart *part = curl_mime_addpart(form);
    curl_mime_name(part, name);
    curl_mime_data(part, value, CURL_ZERO_TERMINATED);
}

/* GET when file is NULL, otherwise POST the route file with its fields. */
static int perform(const char *key, const char *path, const char *file, double speed_kn, double corridor_nm,
                   const char *departure, sealagom_result *out)
{
    CURL *curl;
    curl_mime *form = NULL;
    struct curl_slist *headers = NULL;
    char url[1024], auth[512], num[32];
    CURLcode rc;
    long status = 0;

    memset(out, 0, sizeof(*out));
    out->tokens_remaining = -1;
    if (!key || !*key)
        key = getenv("SEALAGOM_API_KEY");
    snprintf(url, sizeof(url), "%s%s", SEALAGOM_BASE, path);
    curl = curl_easy_init();
    if (!curl) {
        snprintf(out->detail, sizeof(out->detail), "curl_easy_init failed");
        return -1;
    }
    if (key && *key) {
        snprintf(auth, sizeof(auth), "X-API-Token: %s", key);
        headers = curl_slist_append(headers, auth);
    }
    headers = curl_slist_append(headers, "Accept: application/json");
    headers = curl_slist_append(headers, "X-Requested-With: sealagom-kit");
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, SEALAGOM_USER_AGENT);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 60L);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, on_body);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, out);
    curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, on_header);
    curl_easy_setopt(curl, CURLOPT_HEADERDATA, out);
    if (file) {
        curl_mimepart *part;
        form = curl_mime_init(curl);
        part = curl_mime_addpart(form);
        curl_mime_name(part, "file");
        curl_mime_filedata(part, file);
        snprintf(num, sizeof(num), "%g", speed_kn);
        add_field(form, "speed_kn", num);
        snprintf(num, sizeof(num), "%g", corridor_nm);
        add_field(form, "corridor_nm", num);
        if (departure && *departure)
            add_field(form, "departure", departure);
        curl_easy_setopt(curl, CURLOPT_MIMEPOST, form);
    }
    rc = curl_easy_perform(curl);
    if (rc == CURLE_OK) {
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
        out->status = (int)status;
    } else {
        snprintf(out->detail, sizeof(out->detail), "%s", curl_easy_strerror(rc));
    }
    if (form)
        curl_mime_free(form);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    if (rc != CURLE_OK)
        return -1;
    if (status >= 400) {
        pick_detail(out);
        return (int)status;
    }
    return 0;
}

int sealagom_get(const char *key, const char *path_and_query, sealagom_result *out)
{
    return perform(key, path_and_query, NULL, 0, 0, NULL, out);
}

int sealagom_search_warnings(const char *key, const char *query, sealagom_result *out)
{
    char path[2048];
    snprintf(path, sizeof(path), "/api/v2/messages/%s%s", query && *query ? "?" : "", query ? query : "");
    return perform(key, path, NULL, 0, 0, NULL, out);
}

int sealagom_warnings_near(const char *key, double lat, double lon, double radius_nm, sealagom_result *out)
{
    char path[160];
    snprintf(path, sizeof(path), "/api/v2/near/?lat=%.6f&lon=%.6f&radius_nm=%.1f", lat, lon, radius_nm);
    return perform(key, path, NULL, 0, 0, NULL, out);
}

int sealagom_navareas(const char *key, sealagom_result *out)
{
    return perform(key, "/api/v2/navarea/", NULL, 0, 0, NULL, out);
}

int sealagom_feeds(const char *key, sealagom_result *out)
{
    return perform(key, "/api/v2/feeds/", NULL, 0, 0, NULL, out);
}

int sealagom_route_check_file(const char *key, const char *path, double speed_kn, double corridor_nm,
                              const char *departure, sealagom_result *out)
{
    return perform(key, "/api/v2/route/", path, speed_kn, corridor_nm, departure, out);
}

void sealagom_free(sealagom_result *r)
{
    if (r && r->body) {
        free(r->body);
        r->body = NULL;
        r->body_len = 0;
    }
}
