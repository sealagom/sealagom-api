# SeaLagom API: навигационные предупреждения всего мира

Навигационные предупреждения NAVAREA и прибрежные, как их издают координаторы и гидрографические службы, с координатами, контурами и разбором каждого предупреждения. Один ключ, одна строка адреса.

**Ключ.** Зарегистрируйтесь на sealagom.com, откройте Профиль, вкладка API (или войдите через GitHub): ключ бесплатный, на активные предупреждения. Архив, разбор предупреждений, тематические ленты и проверка маршрута входят в платные планы; ответ сам называет план и цену, когда вызову чего-то не хватает.

**Первый вызов.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**Что ещё в этом наборе.** Спецификация OpenAPI, схемы JSON, клиенты на Python и JavaScript, сервер MCP для Claude, Cursor, VS Code, Windsurf и Zed, определения инструментов для ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq и любой OpenAI-совместимой платформы, скрипты для Windows (bat, PowerShell) и shell, GitHub Action для проверки маршрута, порты, береговые станции, суда по названию или MMSI, конвертер маршрутов (RTZ, GPX, KML, CSV, NMEA), бот Telegram, публикация в X, Facebook, Instagram, Telegram.

**Клиенты.** Python, JavaScript, C#, Java, Go, C, PowerShell.

**Ссылки.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

Текст предупреждения первичен; разбор сделан машиной и может ошибаться. Указывайте SeaLagom, www.sealagom.com, там, где показываете данные.

[English README](README.md)
