import os
from datetime import datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from tz import resolve_default_timezone


def test_explicit_parameter_wins():
    """An explicit timezone string should override all other sources."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "America/New_York"}):
        result = resolve_default_timezone(explicit="Asia/Tokyo")
    assert result == ZoneInfo("Asia/Tokyo")


def test_env_var_used_when_no_explicit():
    """If no explicit argument, fall back to DEFAULT_TIMEZONE env var."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Europe/Paris"}, clear=False):
        result = resolve_default_timezone(explicit=None)
    assert result == ZoneInfo("Europe/Paris")


def test_system_timezone_used_when_no_env_var(monkeypatch):
    """If no explicit and no env var, the system local timezone is used —
    BUT only if it resolves to a ZoneInfo. We monkeypatch the resolver to
    keep this test deterministic across platforms (a real Windows host or
    Linux container often returns a non-ZoneInfo tzinfo, which is now
    explicitly downgraded to UTC by the fallback chain)."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    fake_zone = ZoneInfo("Europe/Berlin")
    monkeypatch.setattr("tz._get_system_tz", lambda: fake_zone)

    result = resolve_default_timezone(explicit=None)
    assert result == fake_zone


def test_utc_fallback_when_no_system_tz(monkeypatch):
    """If every other source fails, fall back to UTC."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    monkeypatch.setattr("tz._get_system_tz", lambda: None)
    result = resolve_default_timezone(explicit=None)
    assert result == timezone.utc


def test_invalid_env_var_falls_through_to_system(monkeypatch):
    """A bogus DEFAULT_TIMEZONE should not raise; it should fall through to
    the system path. We monkeypatch _get_system_tz to a known ZoneInfo so
    the test is platform-deterministic."""
    fake_zone = ZoneInfo("Australia/Sydney")
    monkeypatch.setattr("tz._get_system_tz", lambda: fake_zone)
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Not/A_Real_Zone"}, clear=False):
        result = resolve_default_timezone(explicit=None)
    assert result == fake_zone


def test_explicit_empty_string_raises():
    """An empty string explicit should raise ValueError, not silently fall through."""
    with pytest.raises(ValueError, match="must not be blank"):
        resolve_default_timezone(explicit="")


def test_explicit_whitespace_only_raises():
    """A whitespace-only explicit should raise ValueError."""
    with pytest.raises(ValueError, match="must not be blank"):
        resolve_default_timezone(explicit="   ")


def test_non_zoneinfo_system_tz_falls_to_utc(monkeypatch):
    """A system tzinfo that is NOT a ZoneInfo (e.g. a bare datetime.timezone
    offset on Windows or some Linux containers) must NOT be returned. We
    fall through to UTC instead so downstream code never sees ugly display
    names like 'Eastern Daylight Time'."""
    from datetime import timedelta

    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)

    fake_offset = timezone(timedelta(hours=-4), name="EDT-fake")
    monkeypatch.setattr("tz._get_system_tz", lambda: fake_offset)

    result = resolve_default_timezone(explicit=None)
    assert result == timezone.utc, (
        f"Expected UTC, got {result!r} (type {type(result).__name__}). "
        "A non-ZoneInfo system tz should fall through to UTC."
    )
