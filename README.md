# Date-Aware Claude

An MCP server that gives Claude reliable access to the current date and
time.

**Why:** Claude's session-injected date becomes stale in long
conversations, producing wrong answers for phrases like "next Monday"
or "in 3 weeks". This server fixes that by reading the real clock on
every call.

## Tools

| Tool | Purpose |
|------|---------|
| `get_today` | Returns today's date, time, and weekday in a given timezone |
| `convert_timezone` | Converts a datetime from one timezone to another |

## Install — Smithery (one-click)

1. Open Claude Desktop → Connectors → search `date-aware-claude` → **Connect**.
2. Pick your timezone from the dropdown (required).
3. Done. The MCP server is ready.

## Install — Self-hosted

```bash
git clone https://github.com/USERNAME/date-aware-claude
cd date-aware-claude
pip install -e .
```

Then add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "date-aware-claude": {
      "command": "date-aware-claude"
    }
  }
}
```

Self-hosted automatically uses your machine's local timezone. Override
with the `DEFAULT_TIMEZONE` environment variable if desired.

## Usage Tip

If Claude doesn't pick up the tool automatically, prompt it explicitly:
"check today's date before answering". For most date-related phrasing
(tomorrow / next Monday / in 3 weeks / deadline …) Claude will call
`get_today` on its own, based on the tool description.

## Timezone Resolution

When you call `get_today` without a `timezone` argument, the server
resolves which tz to use in this order:

1. Explicit `timezone` argument, if passed.
2. `DEFAULT_TIMEZONE` environment variable (set by Smithery install
   or your own shell).
3. System local timezone (auto-detected when self-hosted).
4. UTC (final fallback).

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## License

MIT
