# SeaLagom API: avisos aos navegantes de todo o mundo

Avisos NAVAREA e costeiros tal como os coordenadores e os serviços hidrográficos os emitem, com posições, contornos e uma análise de cada aviso. Uma chave, um endereço.

**A chave.** Registe-se em sealagom.com, abra Perfil, separador API (ou entre com GitHub): a chave gratuita cobre os avisos em vigor. O arquivo, a análise, os canais temáticos e a verificação de rota fazem parte dos planos pagos; quando falta algo a uma chamada, a resposta indica o plano e o preço.

**A primeira chamada.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**O que mais há neste kit.** Especificação OpenAPI, esquemas JSON, clientes Python e JavaScript, um servidor MCP para Claude, Cursor, VS Code, Windsurf e Zed, definições de ferramentas para ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq e qualquer plataforma compatível com OpenAI, scripts para Windows (bat, PowerShell) e shell, uma GitHub Action que verifica uma rota, portos, estações costeiras, navios por nome ou MMSI, conversor de rotas (RTZ, GPX, KML, CSV, NMEA), bot do Telegram, publicação no X, Facebook, Instagram, Telegram.

**Ligações.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

O texto do aviso é a autoridade; a análise é feita por máquina e pode errar. Cite SeaLagom, www.sealagom.com, onde mostrar os dados.

[English README](README.md)
