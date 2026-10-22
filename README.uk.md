# SeaLagom API: навігаційні попередження всього світу

Навігаційні попередження NAVAREA та прибережні, як їх видають координатори й гідрографічні служби, з координатами, контурами та розбором кожного попередження. Один ключ, одна адреса.

**Ключ.** Зареєструйтеся на sealagom.com, відкрийте Профіль, вкладка API (або увійдіть через GitHub): ключ безкоштовний, на чинні попередження. Архів, розбір попереджень, тематичні стрічки та перевірка маршруту входять до платних планів; відповідь сама називає план і ціну, коли виклику чогось бракує.

**Перший виклик.**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**Що ще в наборі.** Специфікація OpenAPI, схеми JSON, клієнти на Python і JavaScript, сервер MCP для Claude, Cursor, VS Code, Windsurf і Zed, визначення інструментів для ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq і будь-якої OpenAI-сумісної платформи, скрипти для Windows (bat, PowerShell) та shell, GitHub Action для перевірки маршруту, порти, берегові станції, судна за назвою або MMSI, конвертер маршрутів (RTZ, GPX, KML, CSV, NMEA), бот Telegram, публікація в X, Facebook, Instagram, Telegram.

**Посилання.** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

Текст попередження первинний; розбір зроблено машиною, він може помилятися. Вказуйте SeaLagom, www.sealagom.com, там, де показуєте дані.

[English README](README.md)
