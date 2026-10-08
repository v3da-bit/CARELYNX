"""OCR adapter (decision D5). Uses Tesseract only when actually installed; otherwise reports unavailability
explicitly so the affected page is routed to human review instead of silently producing nothing."""

from __future__ import annotations

import io
import shutil
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None  # 0..1, engine-reported mean word confidence


class OcrEngine(Protocol):
    name: str

    @property
    def available(self) -> bool: ...

    def recognize(self, image_bytes: bytes) -> OcrResult: ...


class UnavailableOcr:
    name = "unavailable"

    @property
    def available(self) -> bool:
        return False

    def recognize(self, image_bytes: bytes) -> OcrResult:
        raise RuntimeError("No OCR engine is installed")


import os
from pathlib import Path


def _find_tesseract_binary() -> str | None:
    """Locate the tesseract executable across Windows, macOS, and Linux."""
    # 1. Check explicit environment variable
    custom_path = os.environ.get("TESSERACT_PATH")
    if custom_path and os.path.isfile(custom_path):
        return custom_path

    # 2. Check standard system PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # 3. Check common OS-specific default installation paths
    candidate_paths = [
        # Windows standard locations
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        # macOS Homebrew (Apple Silicon and Intel)
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        # Linux standard locations
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/bin/tesseract",
    ]
    for candidate in candidate_paths:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


class TesseractOcr:
    name = "tesseract"

    def __init__(self) -> None:
        self._binary_path = _find_tesseract_binary()

    @property
    def available(self) -> bool:
        if not self._binary_path:
            return False
        try:
            import PIL  # noqa: F401
            import pytesseract  # noqa: F401
            pytesseract.pytesseract.tesseract_cmd = self._binary_path
        except ImportError:
            return False
        return True

    def recognize(self, image_bytes: bytes) -> OcrResult:
        import pytesseract
        from PIL import Image

        if self._binary_path:
            pytesseract.pytesseract.tesseract_cmd = self._binary_path

        img = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        words = [w for w in data["text"] if w.strip()]
        confs = [float(c) for c, w in zip(data["conf"], data["text"], strict=False) if w.strip() and float(c) >= 0]
        text = pytesseract.image_to_string(img, lang="eng")
        conf = (sum(confs) / len(confs) / 100.0) if confs else None
        return OcrResult(text=text if words else "", confidence=conf)


def get_ocr_engine() -> OcrEngine:
    t = TesseractOcr()
    return t if t.available else UnavailableOcr()
