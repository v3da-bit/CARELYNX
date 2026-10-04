"""Upload validation: content sniffing (magic bytes), size limit, filename sanitization."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.core.errors import AppError, ErrorCode


@dataclass(frozen=True)
class FileKind:
    mime_type: str
    extension: str


PDF = FileKind("application/pdf", "pdf")
PNG = FileKind("image/png", "png")
JPEG = FileKind("image/jpeg", "jpg")

_SIGNATURES: list[tuple[bytes, FileKind]] = [
    (b"%PDF-", PDF),
    (b"\x89PNG\r\n\x1a\n", PNG),
    (b"\xff\xd8\xff", JPEG),
]


def sniff_file_kind(data: bytes) -> FileKind:
    """Trust file *content*, not the client-provided extension or Content-Type."""
    for sig, kind in _SIGNATURES:
        if data.startswith(sig):
            return kind
    raise AppError(
        ErrorCode.UNSUPPORTED_FILE_TYPE, "Only PDF, PNG and JPEG documents are supported.", status_code=415
    )


def check_size(size: int, max_bytes: int) -> None:
    if size == 0:
        raise AppError(ErrorCode.VALIDATION_ERROR, "The uploaded file is empty.", 400)
    if size > max_bytes:
        raise AppError(
            ErrorCode.FILE_TOO_LARGE, f"File exceeds the {max_bytes // (1024 * 1024)} MB limit.", 413
        )


_UNSAFE = re.compile(r"[^A-Za-z0-9._ \-()\u0900-\u097F\u0A80-\u0AFF]")


def sanitize_filename(name: str | None) -> str:
    base = (name or "document").replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFC", base)
    base = "".join(ch for ch in base if unicodedata.category(ch)[0] != "C")
    base = _UNSAFE.sub("_", base).strip(" .") or "document"
    return base[:200]
