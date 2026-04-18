from datetime import datetime
from zoneinfo import ZoneInfo

from server import get_today


def test_get_today_explicit_timezone_tokyo():
    """With an explicit timezone, get_today returns fields in that tz."""
    result = get_today(timezone="Asia/Tokyo")

    assert set(result.keys()) == {"date", "time", "datetime", "weekday", "timezone"}
    assert result["timezone"] == "Asia/Tokyo"

    # Sanity: the returned date should match what 'now' is in Tokyo.
    now_tokyo = datetime.now(ZoneInfo("Asia/Tokyo"))
    assert result["date"] == now_tokyo.strftime("%Y-%m-%d")
    assert result["weekday"] == now_tokyo.strftime("%A")


import os
from unittest.mock import patch


def test_get_today_no_argument_uses_env_var():
    """With no explicit tz, DEFAULT_TIMEZONE env var is used."""
    with patch.dict(os.environ, {"DEFAULT_TIMEZONE": "Europe/London"}, clear=False):
        result = get_today()
    assert result["timezone"] == "Europe/London"


def test_get_today_returns_iso_date_format():
    """date field must be YYYY-MM-DD."""
    result = get_today(timezone="UTC")
    import re
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["date"])
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result["time"])
