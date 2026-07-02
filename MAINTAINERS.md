# Maintainers Guide

Internal notes for maintaining and releasing `date-aware-claude`.

## Updating the Smithery listing

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
