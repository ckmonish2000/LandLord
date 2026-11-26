"""Where paused agent runs are saved, so they survive a server restart."""

import sqlite3
from functools import lru_cache

from langgraph.checkpoint.sqlite import SqliteSaver

from src.config import settings

CHECKPOINT_DB = "agent_state.db"


@lru_cache
def get_checkpointer() -> SqliteSaver:
    """One SQLite file shared by every graph. SqliteSaver locks around each write,
    so worker threads can share the connection."""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DATA_DIR / CHECKPOINT_DB, check_same_thread=False)
    return SqliteSaver(conn)
