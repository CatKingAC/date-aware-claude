import os
import re
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from server import convert_timezone, get_today


def test_get_today_explicit_timezone_tokyo():
    """With an explicit timezone, get_today returns fields in that tz."""
    before = datetime.now(ZoneInfo("Asia/Tokyo"))
    result = get_today(timezone="Asia/Tokyo")
    after = datetime.now(ZoneInfo("Asia/Tokyo"))

    assert set(result.keys()) == {"date", "time", "datetime", "weekday", "timezone"}
    assert result["timezone"] == "Asia/Tokyo"
    assert before.strftime("%Y-%m-%d") <= result["date"] <= after.strftime("%Y-%m-%d")
    assert result["weekday"] in {before.strftime("%A"), after.strftime("%A")}


def test_get_today_no_argument_uses_env_var():
    """With no explicit tz, DEFAULT_TIMEZONE env var is used."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Europe/London"}, clear=False):
        result = get_today()
    assert result["timezone"] == "Europe/London"


def test_get_today_returns_iso_date_format():
    """date field must be YYYY-MM-DD."""
    result = get_today(timezone="UTC")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["date"])
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result["time"])


def test_get_today_no_args_returns_valid_response(monkeypatch):
    """get_today() with no args returns a valid response on the system/UTC fallback path."""
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    result = get_today()
    assert set(result.keys()) == {"date", "time", "datetime", "weekday", "timezone"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["date"])
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result["time"])
    assert result["timezone"]  # non-empty string


def test_convert_timezone_naive_input():
    """Naive datetime + from_timezone → converts to to_timezone."""
    result = convert_timezone(
        datetime_str="2026-04-17 09:00:00",
        from_timezone="America/New_York",
        to_timezone="America/Los_Angeles",
    )
    assert result["original"] == "2026-04-17 09:00:00"
    assert result["original_timezone"] == "America/New_York"
    assert result["converted"] == "2026-04-17 06:00:00"
    assert result["converted_timezone"] == "America/Los_Angeles"
    assert result["weekday"] == "Friday"


def test_convert_timezone_iso_with_offset():
    """ISO 8601 with offset ignores from_timezone."""
    result = convert_timezone(
        datetime_str="2026-04-17T09:00:00-04:00",
        to_timezone="Asia/Tokyo",
        from_timezone="SHOULD_BE_IGNORED",
    )
    # 09:00 EDT → 22:00 JST same day
    assert result["converted"] == "2026-04-17 22:00:00"
    assert result["converted_timezone"] == "Asia/Tokyo"


def test_convert_timezone_missing_from_raises():
    with pytest.raises(ValueError, match="from_timezone is required"):
        convert_timezone(
            datetime_str="2026-04-17 09:00:00",
            to_timezone="UTC",
        )


def test_convert_timezone_dst_fallback_first_occurrence():
    """Ambiguous fall-back hour resolves to the first (pre-DST) occurrence."""
    result = convert_timezone(
        datetime_str="2026-11-01 01:30:00",
        from_timezone="America/New_York",
        to_timezone="UTC",
    )
    # First occurrence is EDT (UTC-4), so 01:30 EDT → 05:30 UTC.
    assert result["converted"] == "2026-11-01 05:30:00"


def test_convert_timezone_z_suffix():
    """ISO 8601 with Z suffix (UTC) converts correctly."""
    result = convert_timezone(
        datetime_str="2026-04-17T13:00:00Z",
        to_timezone="America/New_York",
    )
    # 13:00 UTC → 09:00 EDT (UTC-4) on 2026-04-17
    assert result["converted"] == "2026-04-17 09:00:00"
    assert result["converted_timezone"] == "America/New_York"


def test_convert_timezone_dst_spring_forward_gap():
    """Spring-forward non-existent hour uses pre-transition offset (EST, UTC-5)."""
    result = convert_timezone(
        datetime_str="2026-03-08 02:30:00",
        from_timezone="America/New_York",
        to_timezone="UTC",
    )
    # 02:30 with EST offset (UTC-5) → 07:30 UTC
    assert result["converted"] == "2026-03-08 07:30:00"
