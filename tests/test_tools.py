import os
import re
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from server import get_today


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
