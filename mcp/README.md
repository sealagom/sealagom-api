# SeaLagom MCP server

The warnings as tools in your editor or agent. Any client that speaks MCP works; these are the
configs for the common ones. Install once:

```bash
pip install "mcp[cli]" requests
```

Replace `/path/to/sealagom_mcp.py` with where you put the file and `YOUR_KEY` with a key from
https://www.sealagom.com/profile/?tab=api (sign in with GitHub for one in ten seconds).

## Claude Desktop

`claude_desktop_config.json` (Claude menu, Settings, Developer, Edit Config):

```json
{
  "mcpServers": {
    "sealagom": {
      "command": "python",
      "args": ["/path/to/sealagom_mcp.py"],
      "env": { "SEALAGOM_API_KEY": "YOUR_KEY" }
    }
  }
}
```

## Claude Code

```bash
claude mcp add sealagom -e SEALAGOM_API_KEY=YOUR_KEY -- python /path/to/sealagom_mcp.py
```

## Cursor

`.cursor/mcp.json` in the project (or `~/.cursor/mcp.json` for every project):

```json
{
  "mcpServers": {
    "sealagom": {
      "command": "python",
      "args": ["/path/to/sealagom_mcp.py"],
      "env": { "SEALAGOM_API_KEY": "YOUR_KEY" }
    }
  }
}
```

## VS Code (Copilot agent mode)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "sealagom": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/sealagom_mcp.py"],
      "env": { "SEALAGOM_API_KEY": "${input:sealagom_key}" }
    }
  },
  "inputs": [
    { "id": "sealagom_key", "type": "promptString", "description": "SeaLagom API key", "password": true }
  ]
}
```

## Windsurf

`~/.codeium/windsurf/mcp_config.json`, the same `mcpServers` block as Cursor.

## Zed

`settings.json`, `context_servers`:

```json
{
  "context_servers": {
    "sealagom": {
      "command": { "path": "python", "args": ["/path/to/sealagom_mcp.py"], "env": { "SEALAGOM_API_KEY": "YOUR_KEY" } }
    }
  }
}
```

## What the tools do

| Tool | Asks the API | Typical question |
|---|---|---|
| `search_warnings` | `/api/v2/messages/` with the analysis | "Critical warnings in NAVAREA XI this week" |
| `warnings_near` | `/api/public/warnings/near/` | "Anything within 30 NM of 36.1N 5.4W?" |
| `route_check` | `/api/v2/route/` | "Check this passage: Dover to Gibraltar at 14 knots" |
| `navareas` | `/api/public/navarea-zones/` | "Which NAVAREA covers the Sea of Okhotsk?" |
| `feeds` | `/api/v2/feeds/` | "What themed feeds exist and how big are they?" |

Free keys answer `search_warnings` on active warnings; archives, the analysis fields and the feeds
need a paid plan, and the tool says so in `error`/`hint` when a call is refused.
