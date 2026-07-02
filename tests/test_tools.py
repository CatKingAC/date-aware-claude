import os
import re
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from server import convert_timezone, get_business_days, get_today


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


def test_full_week_inclusive():
    """Mon → Sun (7 calendar days) inclusive = 5 business + 2 weekend."""
    result = get_business_days(
        date_from="2026-04-13",  # Monday
        date_to="2026-04-19",    # Sunday
        inclusive=True,
    )
    assert result["business_days"] == 5
    assert result["weekend_days"] == 2
    assert result["total_days"] == 7
    assert result["date_from"] == "2026-04-13"
    assert result["date_to"] == "2026-04-19"


def test_same_day_weekday():
    """A single weekday counted inclusively = 1 business day."""
    result = get_business_days(
        date_from="2026-04-15",  # Wednesday
        date_to="2026-04-15",
        inclusive=True,
    )
    assert result["business_days"] == 1
    assert result["weekend_days"] == 0
    assert result["total_days"] == 1


def test_same_day_weekend():
    """A single Saturday counted inclusively = 0 business + 1 weekend."""
    result = get_business_days(
        date_from="2026-04-18",  # Saturday
        date_to="2026-04-18",
        inclusive=True,
    )
    assert result["business_days"] == 0
    assert result["weekend_days"] == 1
    assert result["total_days"] == 1


def test_reversed_range_returns_positive():
    """Caller passing date_to < date_from gets a non-negative count
    (internal swap), and dates are echoed back as passed."""
    result = get_business_days(
        date_from="2026-04-30",  # later
        date_to="2026-04-15",    # earlier
        inclusive=True,
    )
    assert result["business_days"] >= 0
    assert result["weekend_days"] >= 0
    assert result["date_from"] == "2026-04-30"
    assert result["date_to"] == "2026-04-15"


def test_echo_dates_unswapped():
    """Even when inputs are reversed, output echoes the original strings."""
    result = get_business_days(
        date_from="2026-04-30",
        date_to="2026-04-15",
        inclusive=True,
    )
    assert result["date_from"] == "2026-04-30", "date_from must be echoed AS PASSED"
    assert result["date_to"] == "2026-04-15", "date_to must be echoed AS PASSED"


def test_inclusive_false_excludes_end():
    """Mon→Fri exclusive (half-open): 4 business days (Fri excluded)."""
    result = get_business_days(
        date_from="2026-04-13",  # Monday
        date_to="2026-04-17",    # Friday
        inclusive=False,
    )
    assert result["business_days"] == 4
    assert result["weekend_days"] == 0
    assert result["total_days"] == 4


def test_q1_2026_known_count():
    """Q1 2026 (Jan 1 – Mar 31, inclusive): independently verified count."""
    # Compute the truth value with an independent loop, NOT using the SUT.
    from datetime import date, timedelta as _td
    expected_biz = 0
    expected_wknd = 0
    cur = date(2026, 1, 1)
    end = date(2026, 3, 31)
    while cur <= end:
        if cur.weekday() >= 5:
            expected_wknd += 1
        else:
            expected_biz += 1
        cur += _td(days=1)

    result = get_business_days(
        date_from="2026-01-01",
        date_to="2026-03-31",
        inclusive=True,
    )
    assert result["business_days"] == expected_biz
    assert result["weekend_days"] == expected_wknd
    assert result["total_days"] == expected_biz + expected_wknd


def test_long_range_8_months():
    """Long-range count (8.5 months) — validates the algorithm doesn't
    miscount on the kind of range an LLM would be likely to fumble."""
    from datetime import date, timedelta as _td
    expected_biz = 0
    cur = date(2026, 1, 15)
    end = date(2026, 9, 30)
    while cur <= end:
        if cur.weekday() < 5:
            expected_biz += 1
        cur += _td(days=1)

    result = get_business_days(
        date_from="2026-01-15",
        date_to="2026-09-30",
        inclusive=True,
    )
    assert result["business_days"] == expected_biz
    assert result["total_days"] == (end - date(2026, 1, 15)).days + 1


def test_invalid_date_raises():
    """Malformed date input raises ValueError (matching convert_timezone)."""
    with pytest.raises(ValueError):
        get_business_days(
            date_from="not-a-date",
            date_to="2026-04-30",
        )
