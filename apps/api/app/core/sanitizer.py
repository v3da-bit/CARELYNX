"""Input sanitization and injection defense utilities.

Provides defense-in-depth against Cross-Site Scripting (XSS), SQL injection patterns,
and malformed control characters across all user-supplied data.
"""

from __future__ import annotations

import html
import re
import unicodedata

# Dangerous HTML tags and attributes
_DANGEROUS_TAGS_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed|applet|meta|link|style|form|base|svg)\b[^>]*>",
    re.IGNORECASE,
)
_DANGEROUS_CLOSING_TAGS_PATTERN = re.compile(
    r"<\s*/\s*(script|iframe|object|embed|applet|meta|link|style|form|base|svg)\s*>",
    re.IGNORECASE,
)
_EVENT_HANDLER_PATTERN = re.compile(
    r"\b(on\w+)\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)",
    re.IGNORECASE,
)
_JAVASCRIPT_URI_PATTERN = re.compile(
    r"(javascript|vbscript|data):",
    re.IGNORECASE,
)

# Common SQL injection tokens used in string concatenation exploits
_SQL_INJECTION_PATTERN = re.compile(
    r"(\b(UNION\s+SELECT|DROP\s+TABLE|ALTER\s+TABLE|INSERT\s+INTO|DELETE\s+FROM)\b|--|\bOR\b\s+['\d]+\s*=\s*['\d]+)",
    re.IGNORECASE,
)


_ALL_TAGS_PATTERN = re.compile(r"<[^>]*>")


def sanitize_plain_text(value: str | None, max_length: int = 1000) -> str:
    """Sanitizes user input by normalizing unicode, removing control characters and null bytes,
    and escaping HTML entities."""
    if not value:
        return ""
    # Normalize unicode to NFC
    text = unicodedata.normalize("NFC", str(value))
    # Strip null bytes and ASCII control characters except newline and tab
    text = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or unicodedata.category(ch)[0] != "C")
    # Strip dangerous HTML tags
    text = _DANGEROUS_TAGS_PATTERN.sub("", text)
    text = _DANGEROUS_CLOSING_TAGS_PATTERN.sub("", text)
    text = _EVENT_HANDLER_PATTERN.sub("", text)
    text = _JAVASCRIPT_URI_PATTERN.sub("", text)
    # Escape remaining HTML characters to prevent XSS
    text = html.escape(text.strip())
    return text[:max_length]


def sanitize_html_free(value: str | None, max_length: int = 500) -> str:
    """Strips all HTML tags completely from the string."""
    if not value:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    text = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or unicodedata.category(ch)[0] != "C")
    text = _ALL_TAGS_PATTERN.sub("", text)
    return html.escape(text.strip())[:max_length]



def contains_sql_injection(value: str) -> bool:
    """Returns True if the string contains obvious SQL injection signatures."""
    if not value:
        return False
    return bool(_SQL_INJECTION_PATTERN.search(value))
