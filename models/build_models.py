"""Make models/*.schema.json from the components of ../openapi.yaml (the site's spec, the source of truth).

    python models/build_models.py

Each file is one JSON Schema (draft 2020-12) holding the model and every component it uses under $defs, so it
validates on its own with no other file. Never edit the JSON files by hand: change the spec and run this again.
"""
import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
MODELS = {
    "warning.schema.json": ("Warning", "One navigational warning as a row of GET /api/v2/messages/, /api/v2/ice/ and /api/v2/feeds/{slug}/."),
    "analysis.schema.json": ("Analysis", "The machine-made analysis of one warning (ai_analysis, Full API)."),
    "route-result.schema.json": ("RouteResult", "The answer of POST /api/v2/route/ and the drop link."),
}
RAW = "https://raw.githubusercontent.com/sealagom/sealagom-api/main/models/"


def refs(node, found):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            found.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            refs(value, found)
    elif isinstance(node, list):
        for value in node:
            refs(value, found)


def closure(schemas, name):
    seen, todo = set(), [name]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        found = set()
        refs(schemas[n], found)
        todo += sorted(found - seen)
    return seen - {name}


def main():
    spec = yaml.safe_load((HERE.parent / "openapi.yaml").read_text(encoding="utf-8"))
    schemas = spec["components"]["schemas"]
    for filename, (name, title_note) in MODELS.items():
        doc = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": RAW + filename,
            "title": name,
            "$comment": "Made by models/build_models.py from openapi.yaml (components/schemas/" + name + "); do not edit.",
            **schemas[name],
        }
        doc["description"] = title_note + " " + schemas[name].get("description", "")
        doc["description"] = doc["description"].strip()
        defs = {d: schemas[d] for d in sorted(closure(schemas, name))}
        if defs:
            doc["$defs"] = defs
        text = json.dumps(doc, indent=2, ensure_ascii=False)
        text = re.sub(r'"#/components/schemas/([A-Za-z0-9_]+)"', lambda m: f'"#/$defs/{m.group(1)}"' if m.group(1) != name else '"#"', text)
        (HERE / filename).write_text(text + "\n", encoding="utf-8")
        print(filename, len(defs), "defs")


if __name__ == "__main__":
    main()
