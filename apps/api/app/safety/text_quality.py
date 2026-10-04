"""Deterministic text-quality scoring (decision D6).

OCR output can be wrong (SAFETY.md §5). We detect typical OCR corruption so that fields read from damaged text
are never presented as verified, independent of what any model claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# letters with an embedded 0/1 (Metf0rmin, dai1y)
_DIGIT_IN_WORD = re.compile(r"^[A-Za-z]+[01]+[A-Za-z]+$")
# numbers with embedded O/o/I/l (5OO, 3O, 1l)
_LETTER_IN_NUMBER = re.compile(r"^\d+[OoIl]+\d*$|^[OoIl]+\d+$")
# '?' touching an alphanumeric (tw?ce, 1?)
_QMARK_IN_TOKEN = re.compile(r"[A-Za-z0-9]\?|\?[A-Za-z0-9]")
_JUNK = re.compile(r"[\ufffd\u25a1\u25af]")

FLAG_SUSPECTED_OCR_ERRORS = "SUSPECTED_OCR_ERRORS"
FLAG_NO_TEXT = "NO_TEXT"
FLAG_LOW_TEXT_DENSITY = "LOW_TEXT_DENSITY"
FLAG_OCR_UNAVAILABLE = "OCR_UNAVAILABLE"


def _strip(token: str) -> str:
    return token.strip(".,;:()[]{}\"'-–—")


def suspicious_tokens(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.split():
        tok = _strip(raw)
        if not tok:
            continue
        if (
            _DIGIT_IN_WORD.match(tok)
            or _LETTER_IN_NUMBER.match(tok)
            or _QMARK_IN_TOKEN.search(tok)
            or _JUNK.search(tok)
        ):
            out.append(tok)
    return out


@dataclass(frozen=True)
class QualityReport:
    score: float
    suspicious: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def line_quality(line: str) -> QualityReport:
    sus = suspicious_tokens(line)
    score = max(0.0, 1.0 - 0.35 * len(sus))
    return QualityReport(round(score, 4), sus, [FLAG_SUSPECTED_OCR_ERRORS] if sus else [])


def page_quality(text: str | None) -> QualityReport:
    if not text or not text.strip():
        return QualityReport(0.0, [], [FLAG_NO_TEXT])
    tokens = [t for t in text.split() if _strip(t)]
    sus = suspicious_tokens(text)
    score = max(0.0, 1.0 - 4.0 * len(sus) / max(1, len(tokens)))
    flags: list[str] = []
    if sus:
        flags.append(FLAG_SUSPECTED_OCR_ERRORS)
    if len(tokens) < 5:
        flags.append(FLAG_LOW_TEXT_DENSITY)
        score = min(score, 0.5)
    return QualityReport(round(score, 4), sus, flags)
