"""Storage backend protocol definition."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for abstract storage backends."""

    def put(self, data: bytes, ext: str) -> str:
        """Store binary data and return an opaque storage key."""
        ...

    def get(self, key: str) -> bytes:
        """Retrieve binary data for the given storage key.

        Raises:
            ValueError: If the storage key is invalid or attempts path traversal.
            FileNotFoundError: If the file does not exist.
        """
        ...

    def delete(self, key: str) -> None:
        """Delete binary data associated with the given key.

        Raises:
            ValueError: If the storage key is invalid or attempts path traversal.
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if a file exists for the given storage key."""
        ...
