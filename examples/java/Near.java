// Warnings in force around 55N 003E (the North Sea), as a table. Java 11+.
//   export SEALAGOM_API_KEY=YOUR_KEY
//   javac -d out java/SeaLagom.java examples/java/Near.java && java -cp out Near
// Without a key the example lists the public feed catalogue instead, which needs no key.
// MIT License, Copyright (c) 2026 SeaLagom.

public final class Near {
    public static void main(String[] args) {
        SeaLagom api = new SeaLagom(null);
        String key = System.getenv("SEALAGOM_API_KEY");
        try {
            if (key == null || key.isBlank()) {
                String feeds = api.feeds();
                System.out.printf("%-10s %8s  %s%n", "Feed", "In force", "Title");
                for (String f : SeaLagom.objects(feeds, "feeds")) {
                    String inForce = SeaLagom.field(f, "in_force");
                    System.out.printf("%-10s %8s  %s%n", SeaLagom.field(f, "slug"), inForce == null ? "" : inForce, SeaLagom.field(f, "title"));
                }
                System.out.println("Set SEALAGOM_API_KEY for the warnings around 55N 003E.");
                return;
            }
            String near = api.warningsNear(55.0, 3.0, 60);
            System.out.println(SeaLagom.field(near, "count") + " warnings in force within 60 NM of 55N 003E");
            System.out.printf("%-14s %-12s %6s  %-9s %s%n", "Region", "Number", "NM", "Severity", "Headline");
            for (String w : SeaLagom.objects(near, "warnings")) {
                String severity = SeaLagom.field(w, "severity"), headline = SeaLagom.field(w, "headline");
                System.out.printf("%-14s %-12s %6s  %-9s %s%n", SeaLagom.field(w, "region_title"), SeaLagom.field(w, "number"),
                    SeaLagom.field(w, "distance_nm"), severity == null ? "" : severity, headline == null ? "" : headline);
            }
            if (api.lastHeaders.containsKey("x-api-tokens-remaining"))
                System.out.println(api.lastHeaders.get("x-api-tokens-remaining").get(0) + " requests left");
        } catch (SeaLagom.Error e) {
            System.err.println("SeaLagom " + e.status + ": " + e.detail);
            System.exit(1);
        }
    }
}
