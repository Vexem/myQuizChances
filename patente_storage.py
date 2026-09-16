"""Durable local storage for in-app test records."""

import json
import os
import tempfile
from pathlib import Path


class StorageError(Exception):
    """Raised when saved application data cannot be read or written."""


def get_storage_path(app_name="AnalisiPatente", base_dir=None):
    """Return the platform data path used by the application."""
    if base_dir is not None:
        root = Path(base_dir)
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / app_name / "records.json"


def _validate_records(records):
    if not isinstance(records, list):
        raise StorageError("Saved records must be a list.")

    validated = []
    for record in records:
        if not isinstance(record, dict) or "data" not in record or "errori" not in record:
            raise StorageError("A saved record has an invalid structure.")
        validated.append({"data": str(record["data"]), "errori": int(record["errori"])})
    return validated


def load_records(path):
    """Load records without changing the source file."""
    storage_path = Path(path)
    if not storage_path.exists():
        return []

    try:
        with storage_path.open("r", encoding="utf-8") as stream:
            return _validate_records(json.load(stream))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise StorageError(f"Unable to read saved records: {error}") from error


def save_records(records, path):
    """Atomically persist records so an interrupted write cannot truncate data."""
    storage_path = Path(path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _validate_records(records)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=storage_path.parent, delete=False) as stream:
            temporary_path = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, storage_path)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise StorageError(f"Unable to save records: {error}") from error
