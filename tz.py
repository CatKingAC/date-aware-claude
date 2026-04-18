"""Timezone resolution for Date-Aware Claude.

Implements the fallback chain documented in the PRD:
  1. Explicit argument from the caller
  2. DEFAULT_TIMEZONE environment variable
  3. System local timezone
  4. UTC
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_default_timezone(explicit: str | None = None) -> ZoneInfo | timezone:
    """Resolve which timezone to use, following the PRD fallback chain."""
    if explicit:
        return ZoneInfo(explicit)

    env_tz = os.environ.get("DEFAULT_TIMEZONE")
    if env_tz:
        try:
            return ZoneInfo(env_tz)
        except ZoneInfoNotFoundError:
            pass

    system_tz = datetime.now().astimezone().tzinfo
    if system_tz is not None:
        return system_tz

    return timezone.utc
