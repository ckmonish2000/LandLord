"""Small helpers shared across modules."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Current time, timezone aware, in UTC. Store and compare times in UTC only."""
    return datetime.now(UTC)
