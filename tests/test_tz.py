import os
from datetime import timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

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
    assert result is not None
    from datetime import tzinfo
    assert isinstance(result, tzinfo)


def test_utc_fallback_when_no_system_tz(monkeypatch):
    """If every other source fails, fall back to UTC."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)

    class FakeDT:
        @staticmethod
        def now():
            class FakeNow:
                def astimezone(self):
                    class FakeAstz:
                        tzinfo = None
                    return FakeAstz()
            return FakeNow()

    monkeypatch.setattr("tz.datetime", FakeDT)
    result = resolve_default_timezone(explicit=None)
    assert result == timezone.utc


def test_invalid_env_var_falls_through_to_system():
    """A bogus DEFAULT_TIMEZONE should not raise; it should fall through."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Not/A_Real_Zone"}, clear=False):
        result = resolve_default_timezone(explicit=None)
    assert result is not None
