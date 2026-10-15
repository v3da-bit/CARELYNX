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


_DANGEROUS_EXTENSIONS = {
    ".exe", ".sh", ".bat", ".cmd", ".vbs", ".js", ".html", ".htm",
    ".php", ".phtml", ".svg", ".py", ".rb", ".jar", ".war", ".cgi", ".pl"
}

_POLYGLOT_PAYLOADS = [
    b"<script",
    b"<?php",
    b"javascript:",
    b"<html",
]



def sniff_file_kind(data: bytes, client_filename: str | None = None) -> FileKind:
    """Trust file *content*, not the client-provided extension or Content-Type."""
    if client_filename:
        lower_name = client_filename.lower()
        for ext in _DANGEROUS_EXTENSIONS:
            if lower_name.endswith(ext) or f"{ext}." in lower_name:
                raise AppError(ErrorCode.UPLOAD_ERROR, f"Prohibited executable or script extension: {ext}", 400)

    matched_kind: FileKind | None = None
    for sig, kind in _SIGNATURES:
        if data.startswith(sig):
            matched_kind = kind
            break

    if matched_kind is None:
        raise AppError(ErrorCode.UPLOAD_ERROR, "Only PDF, PNG and JPEG documents are supported.", 400)

    # Polyglot inspection in the file header
    header_sample = data[:2048].lower()
    for payload in _POLYGLOT_PAYLOADS:
        if payload in header_sample:
            raise AppError(ErrorCode.UPLOAD_ERROR, "Malformed or suspicious active script payload detected in document.", 400)

    return matched_kind


def check_size(size: int, max_bytes: int) -> None:
    if size == 0:
        raise AppError(ErrorCode.UPLOAD_ERROR, "The uploaded file is empty.", 400)
    if size > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise AppError(ErrorCode.UPLOAD_ERROR, f"File exceeds maximum upload size of {limit_mb}MB.", 400)


_UNSAFE = re.compile(r"[^A-Za-z0-9._ \-()\u0900-\u097F\u0A80-\u0AFF]")


def sanitize_filename(name: str | None, expected_ext: str | None = None) -> str:
    base = (name or "document").replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFC", base)
    base = "".join(ch for ch in base if unicodedata.category(ch)[0] != "C")
    base = _UNSAFE.sub("_", base).strip(" .") or "document"
    
    # Strip any dangerous nested extensions
    for ext in _DANGEROUS_EXTENSIONS:
        base = re.sub(re.escape(ext), "_", base, flags=re.IGNORECASE)
        
    base = base[:200]
    if expected_ext:
        # Guarantee extension matches verified kind
        stem = base.rsplit(".", 1)[0] if "." in base else base
        base = f"{stem}.{expected_ext.lstrip('.')}"
    return base

