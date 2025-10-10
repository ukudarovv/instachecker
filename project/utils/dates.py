"""Date utilities."""

from datetime import date, timedelta


def today() -> date:
    """Get today's date."""
    return date.today()


def add_days(d: date, days: int) -> date:
    """Add days to a date."""
    return d + timedelta(days=days)


def clamp_min_days(days: int, min_days: int = 1) -> int:
    """Ensure minimum number of days."""
    return max(days, min_days)
