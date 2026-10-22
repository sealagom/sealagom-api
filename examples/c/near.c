/* Warnings in force around 55N 003E (the North Sea), as a table. C99 with libcurl.
 *   export SEALAGOM_API_KEY=YOUR_KEY
 *   gcc -o near examples/c/near.c c/sealagom.c -lcurl && ./near
 * Without a key the example lists the public feed catalogue instead, which needs no key.
 * The two helpers below read one field and walk one array; they are enough for a table, use cJSON or
 * jansson for more. MIT License, Copyright (c) 2026 SeaLagom. */
#include "../../c/sealagom.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The first value of "key" between obj and end as text: strings unquoted, numbers as written, "" when absent or null. */
static void field(const char *obj, const char *end, const char *key, char *out, size_t n)
{
    char needle[64];
    const char *p;
    size_t i = 0;
    out[0] = '\0';
    snprintf(needle, sizeof(needle), "\"%s\"", key);
    p = strstr(obj, needle);
    if (!p || p >= end || !(p = strchr(p + strlen(needle), ':')))
        return;
    for (p++; p < end && isspace((unsigned char)*p); p++)
        ;
    if (*p == '"') {
        for (p++; p < end && *p != '"' && i < n - 1; p++) {
            if (*p == '\\' && p[1])
                p++;
            out[i++] = *p;
        }
    } else {
        for (; p < end && !strchr(",}]", *p) && i < n - 1; p++)
            out[i++] = *p;
    }
    out[i] = '\0';
    if (strcmp(out, "null") == 0)
        out[0] = '\0';
}

/* The next object of the array "key". Start with *pos = NULL; sets *start and *end (one past the '}');
 * returns 0 when the array is finished or absent. */
static int next_object(const char *json, const char *key, const char **pos, const char **start, const char **end)
{
    const char *p = *pos;
    int depth = 0, in_string = 0;
    char needle[64];
    if (!p) {
        snprintf(needle, sizeof(needle), "\"%s\"", key);
        p = strstr(json, needle);
        if (!p || !(p = strchr(p, '[')))
            return 0;
        p++;
    }
    for (; *p; p++) {
        if (in_string) {
            if (*p == '\\' && p[1])
                p++;
            else if (*p == '"')
                in_string = 0;
        } else if (*p == '"') {
            in_string = 1;
        } else if (*p == '{') {
            if (depth++ == 0)
                *start = p;
        } else if (*p == '}') {
            if (--depth == 0) {
                *end = p + 1;
                *pos = p + 1;
                return 1;
            }
        } else if (*p == ']' && depth == 0) {
            return 0;
        }
    }
    return 0;
}

int main(void)
{
    sealagom_result r;
    const char *key = getenv("SEALAGOM_API_KEY");
    const char *pos = NULL, *start = NULL, *end = NULL;
    char a[64], b[64], c[64], d[200], e[200];
    int rc;

    if (!key || !*key) {
        rc = sealagom_feeds(NULL, &r);
        if (rc != 0) {
            fprintf(stderr, "SeaLagom %d: %s\n", r.status, r.detail);
            sealagom_free(&r);
            return 1;
        }
        printf("%-10s %8s  %s\n", "Feed", "In force", "Title");
        while (next_object(r.body, "feeds", &pos, &start, &end)) {
            field(start, end, "slug", a, sizeof a);
            field(start, end, "in_force", b, sizeof b);
            field(start, end, "title", d, sizeof d);
            printf("%-10s %8s  %s\n", a, b, d);
        }
        puts("Set SEALAGOM_API_KEY for the warnings around 55N 003E.");
        sealagom_free(&r);
        return 0;
    }
    rc = sealagom_warnings_near(key, 55.0, 3.0, 60, &r);
    if (rc != 0) {
        fprintf(stderr, "SeaLagom %d: %s\n", r.status, r.detail);
        sealagom_free(&r);
        return 1;
    }
    field(r.body, r.body + r.body_len, "count", a, sizeof a);
    printf("%s warnings in force within 60 NM of 55N 003E\n", a);
    printf("%-14s %-12s %6s  %-9s %s\n", "Region", "Number", "NM", "Severity", "Headline");
    while (next_object(r.body, "warnings", &pos, &start, &end)) {
        field(start, end, "region_title", a, sizeof a);
        field(start, end, "number", b, sizeof b);
        field(start, end, "distance_nm", c, sizeof c);
        field(start, end, "severity", d, sizeof d);
        field(start, end, "headline", e, sizeof e);
        printf("%-14s %-12s %6s  %-9s %s\n", a, b, c, d, e);
    }
    if (r.tokens_remaining >= 0)
        printf("%ld requests left\n", r.tokens_remaining);
    sealagom_free(&r);
    return 0;
}
