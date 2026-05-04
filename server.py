"""Date-Aware Claude — MCP server.

Exposes two tools: get_today, convert_timezone.
Uses UTC internally; converts to the requested IANA timezone on output.
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Annotated
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from tz import resolve_default_timezone

mcp = FastMCP("date-aware-claude")


@mcp.tool()
def get_today(
    timezone: Annotated[
        str | None,
        Field(description="IANA timezone name, e.g. 'America/New_York' or 'Asia/Tokyo'. Omit to use the server's configured default timezone."),
    ] = None,
) -> dict:
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
    datetime_str: Annotated[
        str,
        Field(description="Datetime to convert. Either 'YYYY-MM-DD HH:MM:SS' (naive, requires from_timezone) or ISO 8601 with offset e.g. '2026-04-17T09:00:00-04:00'."),
    ],
    to_timezone: Annotated[
        str,
        Field(description="Target IANA timezone name, e.g. 'Europe/London' or 'Asia/Shanghai'."),
    ],
    from_timezone: Annotated[
        str | None,
        Field(description="Source IANA timezone name. Required when datetime_str has no UTC offset. Ignored when datetime_str includes an offset."),
    ] = None,
) -> dict:
    """Convert a datetime from one timezone to another.

    Accepts either a naive `YYYY-MM-DD HH:MM:SS` string (requires
    `from_timezone`) or an ISO 8601 string with explicit offset
    (e.g. `2026-04-17T09:00:00-04:00`, in which case `from_timezone`
    is ignored).

    DST handling for naive inputs:
      - Spring-forward non-existent hour → pre-transition offset (standard time)
        is assumed; the wall-clock time is not adjusted.
      - Fall-back ambiguous hour → first (pre-DST) occurrence assumed.
      - For unambiguous behavior, pass ISO 8601 with offset.

    Returns a dict with keys:
      original           — the original datetime string as passed in
      original_timezone  — source timezone label
      converted          — "YYYY-MM-DD HH:MM:SS" in to_timezone
      converted_timezone — the to_timezone string as passed in
      weekday            — full English weekday name in to_timezone
    """
    # Detect ISO 8601 with offset: presence of 'T' and a '+' or '-' after the time portion.
    has_offset = ("T" in datetime_str and (
        "+" in datetime_str.split("T", 1)[1] or "-" in datetime_str.split("T", 1)[1]
    )) or datetime_str.endswith("Z")

    if has_offset:
        # fromisoformat handles "+HH:MM" and (Python 3.11+) trailing "Z".
        parsed = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        source_tz_label = f"UTC{parsed.strftime('%z')[:3]}:{parsed.strftime('%z')[3:]}"
    else:
        if from_timezone is None:
            raise ValueError(
                "from_timezone is required when datetime has no offset"
            )
        naive = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        parsed = naive.replace(tzinfo=ZoneInfo(from_timezone))
        source_tz_label = from_timezone

    target = parsed.astimezone(ZoneInfo(to_timezone))

    return {
        "original": datetime_str,
        "original_timezone": source_tz_label,
        "converted": target.strftime("%Y-%m-%d %H:%M:%S"),
        "converted_timezone": to_timezone,
        "weekday": target.strftime("%A"),
    }


@mcp.tool()
def get_business_days(
    date_from: Annotated[
        str,
        Field(description="Start date in YYYY-MM-DD format."),
    ],
    date_to: Annotated[
        str,
        Field(description="End date in YYYY-MM-DD format."),
    ],
    inclusive: Annotated[
        bool,
        Field(description="If true, both endpoints count. If false, the half-open range [date_from, date_to) is used. Default true (matches Excel NETWORKDAYS)."),
    ] = True,
) -> dict:
    """Count business days (Monday–Friday) between two dates.

    Counts weekdays only — does NOT skip public holidays.

    If `date_to` is earlier than `date_from`, the tool internally swaps
    them and still returns a non-negative `business_days` count. The
    `date_from` and `date_to` fields in the output are echoed back as
    the caller passed them (NOT swapped), so the caller can detect the
    reversed-order case by comparing them.

    Returns a dict with keys:
      date_from      — echoed as passed
      date_to        — echoed as passed
      business_days  — Mon–Fri days in the range (>= 0)
      weekend_days   — Sat + Sun days in the range (>= 0)
      total_days     — business_days + weekend_days
    """
    d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    d_to = datetime.strptime(date_to, "%Y-%m-%d").date()

    # Swap working copies so we always iterate forward.
    if d_to < d_from:
        start, end = d_to, d_from
    else:
        start, end = d_from, d_to

    # Adjust the iteration end based on `inclusive`.
    if inclusive:
        last = end
    else:
        last = end - timedelta(days=1)

    business = 0
    weekend = 0
    cur = start
    while cur <= last:
        # weekday(): Monday=0 ... Sunday=6. Saturday/Sunday are 5 and 6.
        if cur.weekday() >= 5:
            weekend += 1
        else:
            business += 1
        cur += timedelta(days=1)

    return {
        "date_from": date_from,   # echoed as passed (NOT swapped)
        "date_to": date_to,
        "business_days": business,
        "weekend_days": weekend,
        "total_days": business + weekend,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
