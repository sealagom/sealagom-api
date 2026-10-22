# Every platform

One API, one key, one header: `X-API-Token`. Whatever the platform, it is either an MCP client,
an OpenAI-style tool caller, an OpenAPI importer, or an HTTP node. Pick the row that matches.

| Platform | How | File |
|---|---|---|
| Claude Desktop, Claude Code, Cursor, VS Code Copilot (agent mode), Windsurf, Zed, Continue, Cline | MCP server | [../mcp/README.md](../mcp/README.md) |
| OpenAI API, Azure OpenAI, GitHub Copilot SDK | tools (function calling) | [openai-tools.json](openai-tools.json), [openai_compatible.py](openai_compatible.py) |
| DeepSeek, Qwen / Tongyi (DashScope), Moonshot Kimi, Zhipu GLM, Baidu ERNIE (Qianfan), MiniMax, Doubao, Yi | OpenAI-compatible endpoints: same tools, change `LLM_BASE_URL` | [openai_compatible.py](openai_compatible.py) |
| NVIDIA NIM (integrate.api.nvidia.com), NeMo Agent Toolkit | OpenAI-compatible: same tools; the toolkit registers functions from the OpenAPI spec | [openai_compatible.py](openai_compatible.py), [../openapi.yaml](../openapi.yaml) |
| Groq, Mistral, Together, Fireworks, OpenRouter, Ollama, vLLM, LM Studio | OpenAI-compatible | [openai_compatible.py](openai_compatible.py) |
| Gemini (Google AI Studio, Vertex) | function declarations: the same JSON schemas as `parameters` | [openai-tools.json](openai-tools.json) |
| ChatGPT custom GPT (Actions), Dify, Coze, FastGPT, Flowise, Langflow, n8n AI agent | import the OpenAPI spec; auth = API key in header `X-API-Token` | [../openapi.yaml](../openapi.yaml) |
| LangChain, LlamaIndex, CrewAI, AutoGen, Semantic Kernel, Spring AI | wrap `python/sealagom.py` methods as tools, or load the OpenAPI spec | [../python/sealagom.py](../python/sealagom.py) |
| n8n, Zapier, Make, Power Automate, Pipedream, Home Assistant, Node-RED | HTTP request node: GET `https://www.sealagom.com/api/v2/messages/?...` with header `X-API-Token` | below |
| Excel, Power BI, Google Sheets | Power Query "From Web" / `IMPORTDATA` on the JSON, or the RSS and plain-text feeds | below |
| Windows batch, PowerShell, bash, cron, CI | the example scripts; the route drop link for tools that only POST a file | [../examples/](../examples/) |
| ECDIS and bridge software | the route check with the ECDIS route file (RTZ, RT3) and the exports on the site | [../examples/route-check.sh](../examples/route-check.sh) |

## HTTP nodes (n8n, Zapier, Make, Power Automate, Home Assistant)

```
Method   GET
URL      https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true&include_ai_analysis=true&page_size=50
Header   X-API-Token: YOUR_KEY
```

The answer is JSON: `count`, `results[]` (one warning each, see `models/warning.schema.json`),
`meta.warnings` (what the plan left out) and, when something was left out, `meta.upgrade` with the
plan, the price for this request and the checkout links. Poll every 10 to 15 minutes; the API is
updated around the clock. Home Assistant: a `rest` sensor on the same URL with `value_template:
"{{ value_json.count }}"`.

## Spreadsheets

Google Sheets: `=IMPORTDATA("https://www.sealagom.com/feeds/warnings.txt?navarea=1&limit=50")` (no key
needed) or an Apps Script fetch with the header for the JSON. Excel and Power BI: Data, From Web,
Advanced, add the `X-API-Token` header, then expand `results`.

## Telegram, Slack, Teams, e-mail

Use the site's own alerts (Profile, Alerts) or a 20-line bot on top of `python/sealagom.py`:
poll `messages(navarea_id=..., ai_in_force=True)`, remember the `(scope, region_id, number)` keys
you have seen, post the new ones with their `headline` and `url`.

## When a plan does not cover a call

Every refusal (403, 429) and every trimmed answer carries `upgrade`:

```json
{
  "plan": "Full API",
  "monthly_usd": "100.00",
  "yearly_usd": "960.00",
  "unlocks": ["the analysis of every warning ...", "themed feeds (military, cables, offshore, rigs, ice...)", "..."],
  "card": "https://www.sealagom.com/api/subscription/checkout/?plan=full&billing_period=monthly",
  "crypto": { "method": "POST", "url": "https://www.sealagom.com/api/agent/checkout/", "body": { "email": "...", "api": "full", "period": "monthly" } },
  "plans": "https://www.sealagom.com/contributor/plans/#api"
}
```

An agent can show it to its user or follow `crypto` on its own and read the new key from
`status_url`. The price in the block is the price for that request.
