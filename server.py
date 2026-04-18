"""Date-Aware Claude — MCP server.

Exposes two tools: get_today, convert_timezone.
Uses UTC internally; converts to the requested IANA timezone on output.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP

from tz import resolve_default_timezone

mcp = FastMCP("date-aware-claude")


@mcp.tool()
def get_today(timezone: str | None = None) -> dict:
    """Return today's date, current time, and weekday in the resolved timezone.

    Call this before any relative-date computation ("next Monday",
    "in 3 weeks", "end of month"). The session's injected date may be
    stale — this tool always reads the real clock.

    Returns a dict with keys:
      date      — "YYYY-MM-DD"
      time      — "HH:MM:SS"
      datetime  — "YYYY-MM-DD HH:MM:SS"
      weekday   — full English name, e.g. "Friday"
      timezone  — IANA timezone name, e.g. "America/New_York"
    """
    tz = resolve_default_timezone(explicit=timezone)
    now = datetime.now(tz)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": tz.key if isinstance(tz, ZoneInfo) else str(tz),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
