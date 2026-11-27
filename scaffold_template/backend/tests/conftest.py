"""Every test session gets its own throwaway data folder and database."""

import os
import tempfile

# Must run before src is imported: settings are read at import time.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="test-data-")
os.environ.pop("DATABASE_URL", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.database import Base, engine  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture
def client():
    """An API client on an empty database (tables are dropped after each test)."""
    with TestClient(app) as c:  # runs startup: creates the tables
        yield c
    Base.metadata.drop_all(engine)
