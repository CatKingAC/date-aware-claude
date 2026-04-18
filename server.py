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


@mcp.tool()
def convert_timezone(
    datetime: str,
    to_timezone: str,
    from_timezone: str | None = None,
) -> dict:
    """Convert a datetime from one timezone to another.

    Accepts either a naive `YYYY-MM-DD HH:MM:SS` string (requires
    `from_timezone`) or an ISO 8601 string with explicit offset
    (e.g. `2026-04-17T09:00:00-04:00`, in which case `from_timezone`
    is ignored).

    DST handling for naive inputs:
      - Spring-forward missing hour → adjusted forward by 1 hour.
      - Fall-back ambiguous hour → first (pre-DST) occurrence assumed.
      - For unambiguous behavior, pass ISO 8601 with offset.

    Returns a dict with keys:
      original           — the original datetime string as passed in
      original_timezone  — source timezone label
      converted          — "YYYY-MM-DD HH:MM:SS" in to_timezone
      converted_timezone — the to_timezone string as passed in
      weekday            — full English weekday name in to_timezone
    """
    from datetime import datetime as _dt

    dt_str = datetime
    # Detect ISO 8601 with offset: presence of 'T' and a '+' or '-' after the time portion.
    has_offset = ("T" in dt_str and (
        "+" in dt_str.split("T", 1)[1] or "-" in dt_str.split("T", 1)[1]
    )) or dt_str.endswith("Z")

    if has_offset:
        # fromisoformat handles "+HH:MM" and (Python 3.11+) trailing "Z".
        parsed = _dt.fromisoformat(dt_str.replace("Z", "+00:00"))
        source_tz_label = f"UTC{parsed.strftime('%z')[:3]}:{parsed.strftime('%z')[3:]}"
    else:
        if from_timezone is None:
            raise ValueError(
                "from_timezone is required when datetime has no offset"
            )
        naive = _dt.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        parsed = naive.replace(tzinfo=ZoneInfo(from_timezone))
        source_tz_label = from_timezone

    target = parsed.astimezone(ZoneInfo(to_timezone))

    return {
        "original": dt_str if has_offset else parsed.strftime("%Y-%m-%d %H:%M:%S"),
        "original_timezone": source_tz_label,
        "converted": target.strftime("%Y-%m-%d %H:%M:%S"),
        "converted_timezone": to_timezone,
        "weekday": target.strftime("%A"),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
