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
    """If no explicit and no env var, use the system local timezone."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    result = resolve_default_timezone(explicit=None)
    expected = datetime.now().astimezone().tzinfo
    assert result is not None
    assert result == expected


def test_utc_fallback_when_no_system_tz(monkeypatch):
    """If every other source fails, fall back to UTC."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    monkeypatch.setattr("tz._get_system_tz", lambda: None)
    result = resolve_default_timezone(explicit=None)
    assert result == timezone.utc


def test_invalid_env_var_falls_through_to_system():
    """A bogus DEFAULT_TIMEZONE should not raise; it should fall through."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Not/A_Real_Zone"}, clear=False):
        result = resolve_default_timezone(explicit=None)
    expected = datetime.now().astimezone().tzinfo
    assert result == expected


def test_explicit_empty_string_raises():
    """An empty string explicit should raise ValueError, not silently fall through."""
    with pytest.raises(ValueError, match="must not be blank"):
        resolve_default_timezone(explicit="")


def test_explicit_whitespace_only_raises():
    """A whitespace-only explicit should raise ValueError."""
    with pytest.raises(ValueError, match="must not be blank"):
        resolve_default_timezone(explicit="   ")
