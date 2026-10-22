# SeaLagom API: mga babala sa paglalayag ng buong mundo

Mga babala sa paglalayag ng NAVAREA at baybayin, gaya ng inilalabas ng mga coordinator at hydrographic office, may posisyon, hugis at pagsusuri ng bawat babala. Isang key, isang address.

**Key.** Magrehistro sa sealagom.com, buksan ang Profile, tab na API (o mag-sign in gamit ang GitHub): libre ang key para sa mga babalang umiiral. Ang archive, ang pagsusuri, ang mga themed feed at ang pagsusuri ng ruta ay nasa mga bayad na plano; sinasabi mismo ng sagot ang plano at presyo kapag kulang ang isang tawag.

**Unang tawag.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**Ano pa ang nasa kit na ito.** OpenAPI spec, JSON schema, Python at JavaScript client, MCP server para sa Claude, Cursor, VS Code, Windsurf at Zed, tool definition para sa ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq at anumang OpenAI-compatible na platform, script para sa Windows (bat, PowerShell) at shell, GitHub Action na nagsusuri ng ruta, mga daungan, coast station, barko ayon sa pangalan o MMSI, route converter (RTZ, GPX, KML, CSV, NMEA), Telegram bot, pag-post sa X, Facebook, Instagram, Telegram.

**Mga client.** Python, JavaScript, C#, Java, Go, C, PowerShell.

**Mga link.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

Ang teksto ng babala ang awtoridad; gawa ng makina ang pagsusuri at maaaring magkamali. Banggitin ang SeaLagom, www.sealagom.com, kung saan ipinapakita ang datos.

[English README](README.md)
