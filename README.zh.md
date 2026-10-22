# SeaLagom API：全球航行警告

NAVAREA 与沿岸航行警告，按各协调国和海道测量机构发布的原文收录，附坐标、区域轮廓和每条警告的解析。一个密钥，一个地址。

**密钥。** 在 sealagom.com 注册，打开“个人资料”中的 API 页（或用 GitHub 登录）：免费密钥可读取现行警告。历史档案、警告解析、主题订阅源和航线检查属于付费方案；当调用缺少权限时，响应会直接说明所需方案和价格。

**第一次调用。**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**本套件还包含。** OpenAPI 规范、JSON 模式、Python 与 JavaScript 客户端、供 Claude、Cursor、VS Code、Windsurf、Zed 使用的 MCP 服务器，供 ChatGPT、Copilot、Gemini、DeepSeek、通义千问、Kimi、智谱、文心、NVIDIA NIM、Groq 等任何 OpenAI 兼容平台使用的工具定义，Windows（bat、PowerShell）与 shell 脚本，检查航线的 GitHub Action，港口、海岸电台、按船名或 MMSI 查船，航线格式转换（RTZ、GPX、KML、CSV、NMEA），Telegram 机器人，向 X、Facebook、Instagram、Telegram 发布的脚本。

**客户端。** Python、JavaScript、C#、Java、Go、C、PowerShell。

**链接。** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

警告原文为准；解析由机器生成，可能有误。展示数据时请注明来源 SeaLagom，www.sealagom.com。

[English README](README.md)
