"""OCR adapter (decision D5). Uses Tesseract (pytesseract) only when the binary is actually installed;
otherwise
reports unavailability so the page is marked OCR_UNAVAILABLE and routed to human review — never a crash, never
silently empty. Facts read via OCR are never VERIFIED automatically (app.safety.status)."""

from __future__ import annotations

import io
import os
import shutil
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None  # 0..1, engine-reported mean word confidence


class OcrError(OSError):
    """The OCR engine crashed on an image. Processing marks the document FAILED with OCR_ERROR."""


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
        raise OcrError("No OCR engine is installed")


_TESSERACT_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
)


def _find_tesseract_binary() -> str | None:
    """TESSERACT_PATH, then PATH, then common install locations (Windows, macOS, Linux)."""
    custom = os.environ.get("TESSERACT_PATH")
    if custom and os.path.isfile(custom):
        return custom
    return shutil.which("tesseract") or next(
        (p for p in _TESSERACT_CANDIDATES if os.path.isfile(p) and os.access(p, os.X_OK)), None
    )


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
        except ImportError:
            return False
        return True

    def recognize(self, image_bytes: bytes) -> OcrResult:
        try:
            import pytesseract
            from PIL import Image

            pytesseract.pytesseract.tesseract_cmd = self._binary_path
            img = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(img, lang="eng")
        except Exception as exc:  # noqa: BLE001 — any engine/image failure becomes a typed OCR error
            raise OcrError(f"Tesseract failed: {type(exc).__name__}") from exc
        confs = [
            float(c) for c, w in zip(data["conf"], data["text"], strict=False) if w.strip() and float(c) >= 0
        ]
        conf = (sum(confs) / len(confs) / 100.0) if confs else None
        return OcrResult(text=text if confs else "", confidence=conf)


def get_ocr_engine() -> OcrEngine:
    t = TesseractOcr()
    return t if t.available else UnavailableOcr()
