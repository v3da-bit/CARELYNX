"""Prompt Injection Defense and LLM Input Sanitization Guard.

Screens incoming user inputs and extracted document segments for prompt injection,
jailbreak attempts, system override attacks, and instruction exfiltration.
"""

from __future__ import annotations

import logging
import re
from typing import Tuple

from app.core.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

# Heuristic signature patterns for adversarial LLM prompt injections (OWASP LLM01: Prompt Injection)
_INJECTION_PATTERNS = [
    # 1. Direct instruction overrides
    re.compile(
        r"(?i)\b(?:ignore|disregard|forget|override|bypass|cancel)\s+(?:all\s+)?(?:previous|prior|above|existing|system)\s+(?:instructions?|prompts?|rules?|directives?|commands?)\b"
    ),
    re.compile(r"(?i)\b(?:new\s+instructions?|system\s+prompt\s+override|system\s+directive|admin\s+override)\b"),
    # 2. Jailbreak personas / DAN / mode switching
    re.compile(
        r"(?i)\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|DAN\s+mode|jailbreak|developer\s+mode|unrestricted\s+mode|god\s+mode)\b"
    ),
    re.compile(r"(?i)\b(?:do\s+anything\s+now|no\s+filters|bypass\s+safety|disable\s+safety)\b"),
    # 3. System prompt exfiltration
    re.compile(
        r"(?i)\b(?:output|print|reveal|repeat|leak|display|show|exfiltrate)\s+(?:the\s+)?(?:entire\s+)?(?:system\s+prompt|developer\s+instructions?|initial\s+prompt|internal\s+rules?|api\s*keys?|secrets?)\b"
    ),
    # 4. Delimiter injection and ChatML token forgery
    re.compile(r"(?i)<\s*(?:system|assistant|human|im_start|im_end|admin)\s*>"),
    re.compile(r"\[\s*(?:SYSTEM|ASSISTANT|HUMAN|ADMIN|INSTRUCTION)\s*\]"),
    re.compile(r"(?i)\b(?:system:\s*you\s+must|assistant:\s*i\s+will|human:\s*ignore)\b"),
]

# Replacement for suspicious structural tokens
_CONTROL_DELIMITERS = re.compile(r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[SYSTEM\]|\[ASSISTANT\])")

# Replacement for potential secrets, credentials, or leaked tokens in user input
_SECRET_PATTERNS = [
    re.compile(r"\b(?:sk-[a-zA-Z0-9_\-]{20,})\b"),
    re.compile(r"\b(?:ghp_[a-zA-Z0-9]{20,})\b"),
    re.compile(r"\b(?:AIza[0-9A-Za-z\-_]{35})\b"),
    re.compile(r"\b(?:Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*)\b", re.IGNORECASE),
]


def redact_sensitive_data(text: str) -> str:
    """Redacts raw API keys, bearer tokens, or secrets from input before LLM orchestration."""
    if not text or not isinstance(text, str):
        return ""
    result = text
    for secret_pat in _SECRET_PATTERNS:
        result = secret_pat.sub("[REDACTED_SECRET]", result)
    return result


def inspect_prompt_safety(text: str) -> Tuple[bool, str | None]:
    """Inspects text for adversarial prompt injection patterns.
    
    Returns (True, None) if safe, or (False, reason) if adversarial injection pattern is detected.
    """
    if not text or not isinstance(text, str):
        return True, None

    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            reason = f"Adversarial prompt injection pattern detected: '{match.group()}'"
            logger.warning("Prompt safety violation blocked: %s", reason)
            return False, reason

    return True, None


def sanitize_for_prompt(text: str) -> str:
    """Sanitizes text before formatting into prompt templates by defanging delimiters and redacting secrets."""
    if not text or not isinstance(text, str):
        return ""
    # 1. Redact secrets
    redacted = redact_sensitive_data(text)
    # 2. Defang ChatML delimiters
    defanged = _CONTROL_DELIMITERS.sub(r"[REDACTED_DELIMITER]", redacted)
    return defanged


def validate_llm_input(text: str, strict: bool = False) -> str:
    """Validates and sanitizes text for LLM inference.
    
    If strict=True, raises AppError on detected prompt injection.
    Otherwise, defangs dangerous injection payloads.
    """
    is_safe, reason = inspect_prompt_safety(text)
    if not is_safe and strict:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"Input rejected by prompt defense: {reason}", 422)
    return sanitize_for_prompt(text)

