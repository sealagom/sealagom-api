# SeaLagom API: avisos a los navegantes de todo el mundo

Avisos NAVAREA y costeros tal como los emiten los coordinadores y los servicios hidrográficos, con posiciones, contornos y un análisis de cada aviso. Una clave, una dirección.

**La clave.** Regístrese en sealagom.com, abra Perfil, pestaña API (o entre con GitHub): la clave gratuita cubre los avisos en vigor. El archivo, el análisis, los canales temáticos y la comprobación de derrota van con los planes de pago; cuando a una llamada le falta algo, la respuesta nombra el plan y el precio.

**La primera llamada.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**Qué más hay en este kit.** Especificación OpenAPI, esquemas JSON, clientes Python y JavaScript, un servidor MCP para Claude, Cursor, VS Code, Windsurf y Zed, definiciones de herramientas para ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq y cualquier plataforma compatible con OpenAI, scripts para Windows (bat, PowerShell) y shell, una GitHub Action que comprueba una derrota, puertos, estaciones costeras, buques por nombre o MMSI, conversor de derrotas (RTZ, GPX, KML, CSV, NMEA), bot de Telegram, publicación en X, Facebook, Instagram, Telegram.

**Enlaces.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

El texto del aviso es la autoridad; el análisis lo hace una máquina y puede equivocarse. Cite SeaLagom, www.sealagom.com, donde muestre los datos.

[English README](README.md)
