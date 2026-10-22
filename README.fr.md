# SeaLagom API : les avis aux navigateurs du monde entier

Avis NAVAREA et côtiers tels que les coordonnateurs et les services hydrographiques les publient, avec positions, contours et une analyse de chaque avis. Une clé, une adresse.

**La clé.** Inscrivez-vous sur sealagom.com, ouvrez Profil, onglet API (ou connectez-vous avec GitHub) : la clé gratuite couvre les avis en vigueur. Les archives, l'analyse, les flux thématiques et le contrôle de route font partie des formules payantes ; quand il manque quelque chose à un appel, la réponse nomme la formule et le prix.

**Le premier appel.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**Ce que contient aussi ce kit.** La spécification OpenAPI, les schémas JSON, des clients Python et JavaScript, un serveur MCP pour Claude, Cursor, VS Code, Windsurf et Zed, des définitions d'outils pour ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq et toute plateforme compatible OpenAI, des scripts Windows (bat, PowerShell) et shell, une GitHub Action qui contrôle une route, les ports, les stations côtières, les navires par nom ou MMSI, un convertisseur de routes (RTZ, GPX, KML, CSV, NMEA), un bot Telegram, la publication sur X, Facebook, Instagram, Telegram.

**Liens.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

Le texte de l'avis fait foi ; l'analyse est faite par une machine et peut se tromper. Citez SeaLagom, www.sealagom.com, là où vous montrez les données.

[English README](README.md)
