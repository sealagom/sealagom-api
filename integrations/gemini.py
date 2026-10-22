"""SeaLagom as tools for Gemini (Google AI Studio or Vertex AI), with the google-genai SDK.

    pip install google-genai openai requests     # openai only because the tool runner is shared with openai_compatible.py
    export SEALAGOM_API_KEY=...        # https://www.sealagom.com/profile/?tab=api
    export GEMINI_API_KEY=...          # https://aistudio.google.com/apikey  (Vertex: GOOGLE_GENAI_USE_VERTEXAI=true)
    python gemini.py "Which MRCC covers 36N 5W and what is in force within 30 NM?"

The function declarations are built from openai-tools.json (the same JSON schemas, with the keys
Gemini does not take removed), and the calls are run by openai_compatible.call_tool, so the two
loops always offer the same tools.
"""

from __future__ import annotations

import json
import os
import sys

from google import genai
from google.genai import types

sys.path.insert(0, os.path.dirname(__file__))
from openai_compatible import TOOLS, call_tool  # noqa: E402

DROP = {"default", "maximum", "minimum", "minItems", "maxItems"}


def _schema(s):
    """Gemini takes type, description, properties, required, items, enum, nullable."""
    if isinstance(s, dict):
        return {k: _schema(v) for k, v in s.items() if k not in DROP}
    if isinstance(s, list):
        return [_schema(x) for x in s]
    return s


def declarations() -> list[types.FunctionDeclaration]:
    out = []
    for t in TOOLS:
        f = t["function"]
        params = _schema(f.get("parameters") or {"type": "object", "properties": {}})
        if not params.get("properties"):
            params = None  # a tool without arguments
        out.append(types.FunctionDeclaration(name=f["name"], description=f["description"], parameters=params))
    return out


SYSTEM = ("You answer questions about navigational warnings, ports, coast stations and vessels with the SeaLagom tools. "
          "Quote warning numbers and regions. The warning text is the authority; the analysis can be wrong. If a tool "
          "answer carries 'upgrade', say which plan unlocks the missing part and the price it names. Credit SeaLagom, www.sealagom.com.")


def ask(question: str, model: str | None = None) -> str:
    client = genai.Client()
    model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    tools = [types.Tool(function_declarations=declarations())]
    config = types.GenerateContentConfig(tools=tools, system_instruction=SYSTEM,
                                         automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
    contents: list = [types.Content(role="user", parts=[types.Part.from_text(text=question)])]
    for _ in range(6):  # tool rounds
        resp = client.models.generate_content(model=model, contents=contents, config=config)
        calls = resp.function_calls or []
        if not calls:
            return resp.text or ""
        contents.append(resp.candidates[0].content)
        parts = []
        for call in calls:
            result = call_tool(call.name, dict(call.args or {}))
            try:
                payload = json.loads(result)
            except ValueError:
                payload = {"text": result}
            if not isinstance(payload, dict):
                payload = {"result": payload}
            parts.append(types.Part.from_function_response(name=call.name, response=payload))
        contents.append(types.Content(role="user", parts=parts))
    return "Stopped after six tool rounds."


if __name__ == "__main__":
    print(ask(" ".join(sys.argv[1:]) or "Which warnings are in force within 30 NM of 36.1N 5.4W?"))
