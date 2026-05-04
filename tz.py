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


def _get_system_tz() -> "ZoneInfo | timezone | None":
    """Return the local system timezone, or None if detection fails."""
    return datetime.now().astimezone().tzinfo


def resolve_default_timezone(explicit: str | None = None) -> ZoneInfo | timezone:
    """Resolve which timezone to use, following the PRD fallback chain."""
    if explicit is not None:
        stripped = explicit.strip()
        if not stripped:
            raise ValueError(f"explicit timezone must not be blank; got {explicit!r}")
        # ZoneInfoNotFoundError propagates intentionally: an invalid explicit
        # timezone is a caller error and should fail loudly.
        return ZoneInfo(stripped)

    env_tz = os.environ.get("DEFAULT_TIMEZONE")
    if env_tz:
        try:
            return ZoneInfo(env_tz)
        except ZoneInfoNotFoundError:
            pass

    system_tz = _get_system_tz()
    if isinstance(system_tz, ZoneInfo):
        return system_tz
    # system_tz exists but isn't a ZoneInfo (e.g. a bare datetime.timezone
    # offset, or a Windows verbose display name). We can't trust it to
    # produce IANA-style identifiers downstream, so fall through to UTC.
    return timezone.utc
