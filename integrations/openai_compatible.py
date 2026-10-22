"""SeaLagom as tools for any OpenAI-compatible chat API: OpenAI, Azure OpenAI, DeepSeek, Qwen
(DashScope), Moonshot Kimi, Zhipu GLM, Baidu ERNIE (Qianfan), MiniMax, NVIDIA NIM, Groq, Mistral,
Together, OpenRouter, Ollama, vLLM, LM Studio... anything that speaks /v1/chat/completions with tools.

    pip install openai requests
    export SEALAGOM_API_KEY=...            # https://www.sealagom.com/profile/?tab=api
    export LLM_BASE_URL=https://api.deepseek.com/v1   LLM_API_KEY=...   LLM_MODEL=deepseek-chat
    python openai_compatible.py "Which critical warnings are in force in NAVAREA XI this week?"

Change the three LLM_* variables to switch platform; the SeaLagom side stays the same. The tool
definitions are in openai-tools.json; this file is the loop that runs them.

Base URLs: OpenAI https://api.openai.com/v1 | DeepSeek https://api.deepseek.com/v1 |
Qwen https://dashscope.aliyuncs.com/compatible-mode/v1 | Kimi https://api.moonshot.cn/v1 |
Zhipu https://open.bigmodel.cn/api/paas/v4 | NVIDIA NIM https://integrate.api.nvidia.com/v1 |
Groq https://api.groq.com/openai/v1 | Mistral https://api.mistral.ai/v1 | OpenRouter https://openrouter.ai/api/v1 |
Grok (xAI) https://api.x.ai/v1 | Ollama http://localhost:11434/v1 (api key "ollama").
"""

from __future__ import annotations

import json
import os
import sys

import requests
from openai import OpenAI

SEALAGOM = "https://www.sealagom.com"
HEADERS = {"X-API-Token": os.environ.get("SEALAGOM_API_KEY", ""), "Accept": "application/json", "User-Agent": "sealagom-tools/1.0"}
TOOLS = json.load(open(os.path.join(os.path.dirname(__file__), "openai-tools.json"), encoding="utf-8"))


def _params(args: dict) -> list[tuple[str, str]]:
    out = []
    for k, v in args.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out.append((k, "true" if v else "false"))
        elif isinstance(v, list):
            out.extend((k, str(x)) for x in v)
        else:
            out.append((k, str(v)))
    return out


def call_tool(name: str, args: dict) -> str:
    """Run one SeaLagom tool and return a compact JSON string for the model."""
    try:
        if name == "sealagom_search_warnings":
            args.setdefault("include_ai_analysis", True)
            args.setdefault("include_coordinates", True)
            r = requests.get(f"{SEALAGOM}/api/v2/messages/", params=_params(args), headers=HEADERS, timeout=60)
            d = r.json()
            if r.status_code >= 400:
                return json.dumps(d)  # carries detail and, when a plan would unlock it, upgrade {plan, price, links}
            rows = []
            for w in d.get("results") or []:
                ai = w.get("ai_analysis") or {}
                rows.append({"region": w.get("region_title"), "number": w.get("number"), "added_on": w.get("added_on"),
                             "text": (w.get("content_en") or w.get("content") or "")[:900], "positions": w.get("coordinates") if isinstance(w.get("coordinates"), list) else None,
                             "headline": ai.get("headline"), "severity": ai.get("severity"), "status": ai.get("status"), "valid_until": ai.get("valid_until"),
                             "keep_clear_nm": ai.get("keep_clear_nm"), "url": f"{SEALAGOM}/{w.get('scope')}/{w.get('region_id')}/message/{w.get('id')}/"})
            return json.dumps({"count": d.get("count"), "notes": (d.get("meta") or {}).get("warnings"), "upgrade": (d.get("meta") or {}).get("upgrade"), "warnings": rows}, ensure_ascii=False)
        if name == "sealagom_warnings_near":
            r = requests.get(f"{SEALAGOM}/api/v2/near/", params=_params(args), headers=HEADERS, timeout=60)
            return r.text[:60000]
        if name == "sealagom_route_check":
            r = requests.post(f"{SEALAGOM}/api/v2/route/", json=args, headers=HEADERS, timeout=120)
            return r.text[:80000]
        if name == "sealagom_navareas":
            d = requests.get(f"{SEALAGOM}/api/v2/navarea-zones/", headers=HEADERS, timeout=60).json()
            return json.dumps([{k: (f.get("properties") or {}).get(k) for k in ("id", "name", "coordinator", "navarea_id", "in_force")} for f in d.get("features") or []])
        if name == "sealagom_feeds":
            return requests.get(f"{SEALAGOM}/api/v2/feeds/", headers=HEADERS, timeout=60).text[:40000]
        if name == "sealagom_find_port":
            if args.pop("top", False):
                args.update({"sort": "rank", "top": 1})
            return requests.get(f"{SEALAGOM}/api/v2/ports/", params=_params({**args, "page_size": 20}), headers=HEADERS, timeout=60).text[:30000]
        if name == "sealagom_port_details":
            d = requests.get(f"{SEALAGOM}/api/v2/ports/{args.get('slug', '')}/", headers=HEADERS, timeout=60).json()
            (d.get("port") or {}).pop("images", None)
            return json.dumps(d, ensure_ascii=False, default=str)[:40000]
        if name == "sealagom_stations_near":
            return requests.get(f"{SEALAGOM}/api/v2/stations/near/", params=_params(args), headers=HEADERS, timeout=60).text[:30000]
        if name == "sealagom_find_vessel":
            return requests.get(f"{SEALAGOM}/api/v2/vessels/", params=_params({**args, "limit": 30}), headers=HEADERS, timeout=60).text[:40000]
        if name == "sealagom_convert_route":
            body = {"waypoints": [{"lat": p[0], "lon": p[1]} for p in args.get("waypoints") or []], "name": args.get("name") or "Route"}
            return requests.post(f"{SEALAGOM}/api/v2/route/convert/", params={"to": args.get("to") or "rtz"}, json=body, headers=HEADERS, timeout=60).text[:200000]
        if name == "sealagom_rigs":
            return requests.get(f"{SEALAGOM}/api/v2/rigs/", headers=HEADERS, timeout=60).text[:40000]
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)[:200]})
    return json.dumps({"error": f"unknown tool {name}"})


def ask(question: str, *, model: str | None = None) -> str:
    client = OpenAI(base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"), api_key=os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or "ollama")
    model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
    messages = [
        {"role": "system", "content": "You answer questions about navigational warnings with the SeaLagom tools. Quote warning numbers and regions. "
                                      "The warning text is the authority; the analysis can be wrong. If a tool answer carries 'upgrade', tell the user "
                                      "which plan unlocks the missing part and the price it names. Credit SeaLagom, www.sealagom.com."},
        {"role": "user", "content": question},
    ]
    for _ in range(6):  # tool rounds
        resp = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, tool_choice="auto")
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content or ""
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": call_tool(call.function.name, args)})
    return "Stopped after six tool rounds."


if __name__ == "__main__":
    print(ask(" ".join(sys.argv[1:]) or "What are the critical warnings in force in NAVAREA I?"))
