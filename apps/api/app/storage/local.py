"""Local filesystem storage backend with path traversal protection and isolated keys."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import get_settings
from app.storage.base import StorageBackend


class LocalPrivateStorage:
    """Stores files in an isolated local directory with non-predictable UUID keys."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        if root_dir is None:
            self.root = get_settings().storage_path
        else:
            self.root = Path(root_dir)
        self.root = self.root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        if not key or ".." in key or key.startswith(("/", "\\")):
            raise ValueError(f"Invalid storage key: {key}")
        path = (self.root / key).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            raise ValueError(f"Path traversal detected: {key}") from None
        return path

    def put(self, data: bytes, ext: str) -> str:
        clean_ext = ext.strip()
        if clean_ext and not clean_ext.startswith("."):
            clean_ext = f".{clean_ext}"
        key = f"{uuid.uuid4().hex}{clean_ext}"
        path = self._resolve_path(key)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        path = self._resolve_path(key)
        if not path.is_file():
            raise FileNotFoundError(f"Stored file not found for key: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve_path(key)
        if path.is_file():
            path.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        try:
            path = self._resolve_path(key)
            return path.is_file()
        except ValueError:
            return False


def get_storage() -> StorageBackend:
    """FastAPI dependency for accessing the configured StorageBackend."""
    return LocalPrivateStorage(get_settings().storage_path)
