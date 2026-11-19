import json
import uuid
from pathlib import Path
from threading import Lock

from src.config import settings

# One lock per file, shared by every repository instance that uses that file.
_locks: dict[Path, Lock] = {}
_locks_guard = Lock()


def _lock_for(path: Path) -> Lock:
    with _locks_guard:
        return _locks.setdefault(path, Lock())


class JsonCollection:
    """A collection stored as a JSON list in data/<name>.json."""

    def __init__(self, name: str, data_dir: Path = settings.DATA_DIR):
        self.path = data_dir / f"{name}.json"
        self._lock = _lock_for(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if not self.path.exists():
                self._write([])

    def _read(self) -> list[dict]:
        with self.path.open() as f:
            return json.load(f)

    def _write(self, records: list[dict]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(records, f, indent=2)
        tmp.replace(self.path)

    def get_all(self) -> list[dict]:
        return self._read()

    def get_by_id(self, record_id: str) -> dict | None:
        return self.find_one("id", record_id)

    def find_one(self, field: str, value) -> dict | None:
        return next((r for r in self._read() if r.get(field) == value), None)

    def create(self, record: dict) -> dict:
        with self._lock:
            records = self._read()
            new = {"id": str(uuid.uuid4()), **record}
            records.append(new)
            self._write(records)
            return new

    def update(self, record_id: str, fields: dict) -> dict | None:
        with self._lock:
            records = self._read()
            for r in records:
                if r["id"] == record_id:
                    r.update({k: v for k, v in fields.items() if k != "id"})
                    self._write(records)
                    return r
            return None

    def upsert(self, field: str, value, fields: dict) -> dict:
        """Update the first record where record[field] == value, or create it."""
        with self._lock:
            records = self._read()
            for r in records:
                if r.get(field) == value:
                    r.update({k: v for k, v in fields.items() if k != "id"})
                    self._write(records)
                    return r
            new = {"id": str(uuid.uuid4()), field: value, **fields}
            records.append(new)
            self._write(records)
            return new

    def delete(self, record_id: str) -> bool:
        with self._lock:
            records = self._read()
            remaining = [r for r in records if r["id"] != record_id]
            if len(remaining) == len(records):
                return False
            self._write(remaining)
            return True
