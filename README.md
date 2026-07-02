# Date-Aware Claude

[![CI](https://github.com/CatKingAC/date-aware-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/CatKingAC/date-aware-claude/actions/workflows/ci.yml)

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
| `get_business_days` | Counts Mon–Fri weekdays between two dates (no holiday handling) |

## Install — Smithery (one-click)

1. Open Claude Desktop → Connectors → search `date-aware-claude` → **Connect**.
2. Pick your timezone from the dropdown (required).
3. Done. The MCP server is ready.

## Install — Self-hosted

```bash
git clone https://github.com/CatKingAC/date-aware-claude
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

## Maintainers — Updating the Smithery listing

This server is published to Smithery as an **external / static-card** entry.
Smithery does **not** build from this repo and does **not** auto-deploy on
`git push` here. Instead it reads a hand-maintained metadata file:

```
https://catkingac.github.io/.well-known/mcp/server-card.json
```

That file lives in a **separate** repo: `CatKingAC/catkingac.github.io`
(GitHub Pages serves it at the domain root — Smithery only checks
`/.well-known/mcp/server-card.json` at the root, not under a subpath).

**Whenever you change the tools** (add/remove a tool, change parameters or
return shape), update the listing with this cycle:

1. Edit `.well-known/mcp/server-card.json` in the **`catkingac.github.io`**
   repo — keep `serverInfo.version`, the tool list, `inputSchema`, and
   `outputSchema` in sync with `server.py`. (Keep the copy in this repo's
   `.well-known/` identical, for reference.)
2. Commit + push, then wait ~1 min for GitHub Pages to rebuild. Verify:
   ```bash
   curl -s https://catkingac.github.io/.well-known/mcp/server-card.json
   ```
3. Re-run the publish command so Smithery re-scans the card:
   ```bash
   npx @smithery/cli mcp publish "https://catkingac.github.io" \
     -n @caj201100/date-aware-claude \
     --config-schema ./smithery-schema.json
   ```
   A successful scan logs `Server metadata discovered (... server card: N tools)`.

> ⚠️ The card is metadata, not generated from code — it can drift from
> `server.py`. Treat updating it as a required step of any release that
> touches the tool surface.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the release history.

## License

MIT
