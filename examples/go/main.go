// Warnings in force around 55N 003E (the North Sea), as a table. Go 1.21+.
//
//	export SEALAGOM_API_KEY=YOUR_KEY
//	cd examples/go && go run .
//
// Without a key the example lists the public feed catalogue instead, which needs no key.
// MIT License, Copyright (c) 2026 SeaLagom.
package main

import (
	"fmt"
	"os"

	sealagom "github.com/sealagom/sealagom-api/go"
)

func str(m map[string]any, key string) string {
	v, ok := m[key]
	if !ok || v == nil {
		return ""
	}
	if f, ok := v.(float64); ok {
		return fmt.Sprintf("%.1f", f)
	}
	return fmt.Sprint(v)
}

func rows(m map[string]any, key string) []map[string]any {
	var out []map[string]any
	if list, ok := m[key].([]any); ok {
		for _, item := range list {
			if row, ok := item.(map[string]any); ok {
				out = append(out, row)
			}
		}
	}
	return out
}

func main() {
	api := sealagom.New("")
	if api.Key == "" {
		feeds, err := api.Feeds()
		if err != nil {
			fmt.Fprintln(os.Stderr, "SeaLagom:", err)
			os.Exit(1)
		}
		fmt.Printf("%-10s %8s  %s\n", "Feed", "In force", "Title")
		for _, f := range rows(feeds, "feeds") {
			inForce := ""
			if n, ok := f["in_force"].(float64); ok {
				inForce = fmt.Sprintf("%d", int(n))
			}
			fmt.Printf("%-10s %8s  %s\n", str(f, "slug"), inForce, str(f, "title"))
		}
		fmt.Println("Set SEALAGOM_API_KEY for the warnings around 55N 003E.")
		return
	}
	near, err := api.WarningsNear(55.0, 3.0, 60)
	if err != nil {
		fmt.Fprintln(os.Stderr, "SeaLagom:", err)
		os.Exit(1)
	}
	fmt.Printf("%v warnings in force within 60 NM of 55N 003E\n", near["count"])
	fmt.Printf("%-14s %-12s %6s  %-9s %s\n", "Region", "Number", "NM", "Severity", "Headline")
	for _, w := range rows(near, "warnings") {
		ai, _ := w["ai"].(map[string]any)
		fmt.Printf("%-14s %-12s %6s  %-9s %s\n", str(w, "region_title"), str(w, "number"), str(w, "distance_nm"), str(ai, "severity"), str(ai, "headline"))
	}
	if left := api.LastHeaders.Get("X-API-Tokens-Remaining"); left != "" {
		fmt.Println(left, "requests left")
	}
}
