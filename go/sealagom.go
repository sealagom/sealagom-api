// Package sealagom is the SeaLagom API client for Go 1.21+. No dependencies: net/http and encoding/json.
// MIT License, Copyright (c) 2026 SeaLagom. See LICENSE in the repository root.
//
//	api := sealagom.New("YOUR_KEY")                       // or "" for the SEALAGOM_API_KEY environment variable
//	page, err := api.SearchWarnings(sealagom.Params{"navarea_id": 1, "ai_in_force": true})
//	near, err := api.WarningsNear(55.0, 3.0, 60)          // warnings in force within 60 NM
//	check, err := api.RouteCheckFile("passage.rtz", 12, 15, "")
//	check2, err := api.RouteCheck([][2]float64{{51.0, 1.5}, {36.1, -5.4}}, 14, 10, "")
//
// Lists are slices: Params{"ai_severity": []string{"critical", "high"}}. Answers are the JSON as served, as
// map[string]any (Do decodes into your own struct). Errors are *Error with the HTTP status and the server's
// detail (401 no or wrong key, 403 not in the plan, 429 allowance reached). Without a key only Feeds answers.
package sealagom

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"time"
)

const (
	Base      = "https://www.sealagom.com"
	UserAgent = "sealagom-go/1.0"
)

// Params are query parameters; nil values are left out, slices repeat the key.
type Params map[string]any

// Error is an HTTP error with the server's detail text.
type Error struct {
	Status int
	Detail string
}

func (e *Error) Error() string { return fmt.Sprintf("%d: %s", e.Status, e.Detail) }

// Client talks to one base URL with one key.
type Client struct {
	Key         string
	Base        string
	HTTP        *http.Client
	LastHeaders http.Header
}

// New makes a client; an empty key reads SEALAGOM_API_KEY. Timeout 60 s.
func New(key string) *Client {
	if key == "" {
		key = os.Getenv("SEALAGOM_API_KEY")
	}
	return &Client{Key: strings.TrimSpace(key), Base: Base, HTTP: &http.Client{Timeout: 60 * time.Second}}
}

// Query encodes Params the way the API expects.
func Query(p Params) string {
	q := url.Values{}
	for k, v := range p {
		if v == nil {
			continue
		}
		rv := reflect.ValueOf(v)
		if rv.Kind() == reflect.Slice || rv.Kind() == reflect.Array {
			for i := 0; i < rv.Len(); i++ {
				q.Add(k, fmt.Sprint(rv.Index(i).Interface()))
			}
		} else {
			q.Add(k, fmt.Sprint(v))
		}
	}
	if len(q) == 0 {
		return ""
	}
	return "?" + q.Encode()
}

// Do sends a request with the key and the kit headers and decodes the JSON answer into out (a pointer).
func (c *Client) Do(req *http.Request, out any) error {
	if c.Key != "" {
		req.Header.Set("X-API-Token", c.Key)
	}
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Requested-With", "sealagom-kit")
	r, err := c.HTTP.Do(req)
	if err != nil {
		return err
	}
	defer r.Body.Close()
	c.LastHeaders = r.Header
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}
	if r.StatusCode >= 400 {
		var e struct {
			Detail string `json:"detail"`
		}
		if json.Unmarshal(body, &e) != nil || e.Detail == "" {
			e.Detail = string(body[:min(len(body), 200)])
		}
		return &Error{Status: r.StatusCode, Detail: e.Detail}
	}
	return json.Unmarshal(body, out)
}

// Get is any GET under the base URL, decoded into a map.
func (c *Client) Get(path string, p Params) (map[string]any, error) {
	return c.send(http.MethodGet, path+Query(p), nil, "")
}

func (c *Client) send(method, path string, body io.Reader, contentType string) (map[string]any, error) {
	req, err := http.NewRequest(method, c.Base+path, body)
	if err != nil {
		return nil, err
	}
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	var out map[string]any
	if err := c.Do(req, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// SearchWarnings is GET /api/v2/messages/: navarea_id, country, q, date_from, date_to, ai_severity, ai_in_force,
// include_ai_analysis, topic, page, page_size... Answer: count, next, results[].
func (c *Client) SearchWarnings(p Params) (map[string]any, error) { return c.Get("/api/v2/messages/", p) }

// WarningsNear is GET /api/v2/near/: warnings in force within radiusNm (up to 200) of a position. Answer: count,
// warnings[] with region_title, number, distance_nm, nearest, ai (headline, severity, valid_until).
func (c *Client) WarningsNear(lat, lon, radiusNm float64) (map[string]any, error) {
	return c.Get("/api/v2/near/", Params{"lat": lat, "lon": lon, "radius_nm": radiusNm})
}

// Navareas is GET /api/v2/navarea/: the 21 NAVAREAs with their region ids.
func (c *Client) Navareas() (map[string]any, error) { return c.Get("/api/v2/navarea/", nil) }

// Feeds is GET /api/v2/feeds/: every feed with its endpoint and warnings in force (no key needed). Answer: feeds[].
func (c *Client) Feeds() (map[string]any, error) { return c.Get("/api/v2/feeds/", nil) }

// Feed is GET /api/v2/feeds/{slug}/: one themed feed (military, cables, offshore, survey, hazards, ice...).
func (c *Client) Feed(slug string, p Params) (map[string]any, error) {
	return c.Get("/api/v2/feeds/"+url.PathEscape(slug)+"/", p)
}

// RouteCheck is POST /api/v2/route/ with waypoints {lat, lon}; departure ISO UTC or "". Answer: route_nm,
// navareas[], count, results[] (distance_nm, along_nm, verdict, ai).
func (c *Client) RouteCheck(waypoints [][2]float64, speedKn, corridorNm float64, departure string) (map[string]any, error) {
	wps := make([]map[string]float64, len(waypoints))
	for i, w := range waypoints {
		wps[i] = map[string]float64{"lat": w[0], "lon": w[1]}
	}
	body := map[string]any{"waypoints": wps, "speed_kn": speedKn, "corridor_nm": corridorNm}
	if departure != "" {
		body["departure"] = departure
	}
	buf, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	return c.send(http.MethodPost, "/api/v2/route/", bytes.NewReader(buf), "application/json")
}

// RouteCheckFile is POST /api/v2/route/ with a route file (RTZ, RT3, GPX, KML, CSV, NMEA; up to 5 MB).
func (c *Client) RouteCheckFile(path string, speedKn, corridorNm float64, departure string) (map[string]any, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var buf bytes.Buffer
	form := multipart.NewWriter(&buf)
	part, err := form.CreateFormFile("file", filepath.Base(path))
	if err != nil {
		return nil, err
	}
	part.Write(data)
	form.WriteField("speed_kn", fmt.Sprint(speedKn))
	form.WriteField("corridor_nm", fmt.Sprint(corridorNm))
	if departure != "" {
		form.WriteField("departure", departure)
	}
	form.Close()
	return c.send(http.MethodPost, "/api/v2/route/", &buf, form.FormDataContentType())
}
