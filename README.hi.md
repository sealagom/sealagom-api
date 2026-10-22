# SeaLagom API: पूरी दुनिया की नौवहन चेतावनियाँ

NAVAREA और तटीय नौवहन चेतावनियाँ, जैसी समन्वयक और जलसर्वेक्षण प्राधिकरण जारी करते हैं, स्थिति, आकृति और हर चेतावनी के विश्लेषण के साथ। एक कुंजी, एक पता।

**कुंजी।** sealagom.com पर पंजीकरण करें, प्रोफ़ाइल में API टैब खोलें (या GitHub से साइन इन करें): मुफ़्त कुंजी सक्रिय चेतावनियों के लिए है। अभिलेख, विश्लेषण, विषय-फ़ीड और मार्ग जाँच सशुल्क योजनाओं में हैं; जब किसी कॉल को अधिक चाहिए, उत्तर स्वयं योजना और कीमत बताता है।

**पहली कॉल।**

```bash
curl "https://www.sealagom.com/api/v2/messages/?navarea_id=1&ai_in_force=true" -H "X-API-Token: YOUR_KEY"
```

```python
from sealagom import SeaLagom          # python/sealagom.py
api = SeaLagom("YOUR_KEY")
for w in api.messages(navarea_id=1, ai_in_force=True):
    print(w["number"], w["content_en"][:80])
```

**इस किट में और क्या है।** OpenAPI विनिर्देश, JSON स्कीमा, Python और JavaScript क्लाइंट, Claude, Cursor, VS Code, Windsurf और Zed के लिए MCP सर्वर, ChatGPT, Copilot, Gemini, DeepSeek, Qwen, Kimi, NVIDIA NIM, Groq और किसी भी OpenAI-संगत प्लेटफ़ॉर्म के लिए टूल परिभाषाएँ, Windows (bat, PowerShell) और shell स्क्रिप्ट, मार्ग जाँचने वाला GitHub Action, बंदरगाह, तटीय रेडियो स्टेशन, नाम या MMSI से जहाज़, मार्ग फ़ाइल परिवर्तक (RTZ, GPX, KML, CSV, NMEA), Telegram बॉट, X, Facebook, Instagram, Telegram पर पोस्ट करने की स्क्रिप्ट।

**क्लाइंट।** Python, JavaScript, C#, Java, Go, C, PowerShell।

**लिंक।** https://www.sealagom.com/profile/?tab=api · https://www.sealagom.com/developers/ · https://www.sealagom.com/github/tools/ · openapi.yaml · mcp/README.md · integrations/PLATFORMS.md · FEEDS.md

चेतावनी का मूल पाठ ही प्रामाणिक है; विश्लेषण मशीन से बना है और ग़लत हो सकता है। डेटा दिखाते समय SeaLagom, www.sealagom.com का उल्लेख करें।

[English README](README.md)
