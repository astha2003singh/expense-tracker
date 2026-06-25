"""Date parsing utilities with natural language support."""

from __future__ import annotations

from datetime import datetime, timedelta

from dateutil import parser as dateutil_parser

NATURAL_DATES = {
    "today": lambda: datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
    "yesterday": lambda: (datetime.now() - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ),
    "tomorrow": lambda: (datetime.now() + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ),
}


def parse_date(date_str: str) -> datetime:
    """Parse a date string supporting both ISO format and natural language.

    Supported formats:
        - YYYY-MM-DD (e.g., "2026-05-14")
        - Natural language: "today", "yesterday", "tomorrow"
        - Flexible formats via dateutil: "May 14", "14/05/2026", etc.

    Args:
        date_str: The date string to parse.

    Returns:
        A datetime object.

    Raises:
        ValueError: If the date string cannot be parsed.
    """
    normalized = date_str.strip().lower()

    # Check natural language dates
    if normalized in NATURAL_DATES:
        return NATURAL_DATES[normalized]()

    # Try dateutil parser (handles YYYY-MM-DD and many other formats)
    try:
        return dateutil_parser.parse(date_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Cannot parse date '{date_str}'. "
            f"Use YYYY-MM-DD format or natural language (today, yesterday)."
        ) from exc
