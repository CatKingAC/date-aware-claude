# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-05-04

### Added
- `get_business_days(date_from, date_to, inclusive=True)` — counts Monday–Friday
  weekdays between two dates. Returns a non-negative count even when the input
  range is reversed (auto-swaps internally; echoes input dates unswapped so a
  caller can detect reversal). Counts weekdays only — does NOT skip public
  holidays.

### Fixed
- `get_today` no longer returns OS-level display names like `"Eastern Daylight
  Time"` when the resolved timezone cannot be expressed as an IANA identifier.
  The fallback chain now requires `zoneinfo.ZoneInfo` specifically and falls
  through to UTC otherwise. Self-hosted users on systems where the local tz
  auto-detects to a `ZoneInfo` see no behavior change.

### Operational
- Verified `DEFAULT_TIMEZONE` env-var passthrough on Smithery hosting (see
  Task 6 of the v1.1 implementation plan).

## [1.0.0] — 2026-04-18

### Added
- Initial release.
- `get_today(timezone=None)` — returns today's date, time, weekday in the
  resolved timezone.
- `convert_timezone(datetime, to_timezone, from_timezone=None)` — converts a
  naive or ISO-8601 datetime between IANA timezones; documents DST behavior.
- Smithery one-click install with a 14-timezone enum dropdown
  (America/New_York, Europe/London, Asia/Shanghai, etc.).
- Self-hosted GitHub install path with auto-detected system timezone.
