"""Small helpers shared across modules."""

from datetime import UTC, datetime


def now_iso() -> str:
    """Current time in UTC as ISO 8601, the format every record's timestamps use."""
    return datetime.now(UTC).isoformat()
