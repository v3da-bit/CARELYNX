"""Safety-checked translation of patient-facing text (SAFETY.md §5).

`translate_texts` masks drug names, doses, dates, times, phone numbers and every other number with placeholder
tokens before any text leaves the process, then unmasks and verifies the result: each placeholder must come
back
exactly once and the digits of the output must equal the digits of the source. Anything that fails → None (the
caller shows English with "translation unavailable"). Network/engine failures never raise.

Engine order: Google Cloud Translation v2 (if GOOGLE_TRANSLATE_API_KEY) → the configured openai_compat LLM
(only
when INFERENCE_PROVIDER is not rule_based; prompt `translation_v1`) → free Google web endpoint via
deep-translator → None. Items an engine fails on are retried on the next engine. Patient text is never logged.
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import re
import sqlite3
from collections.abc import Awaitable, Callable, Sequence

import httpx

from app.ai.factory import get_inference_provider
from app.ai.prompts import load_prompt
from app.core.config import get_settings
from app.models.enums import Language

logger = logging.getLogger(__name__)

GOOGLE_TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"
TOTAL_TIMEOUT_S = 10.0  # whole batch, all engines
LANGUAGE_NAMES = {
    Language.HI: "Hindi",
    Language.GU: "Gujarati",
    Language.MR: "Marathi",
    Language.TA: "Tamil",
    Language.TE: "Telugu",
}

_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_PROTECTED = (
    r"\b\d{4}-\d{2}-\d{2}\b",  # ISO date
    rf"\b\d{{1,2}}\s+{_MON},?\s+\d{{4}}\b",  # 14 Oct 2026
    rf"\b{_MON}\s+\d{{1,2}},?\s+\d{{4}}\b",  # Oct 14, 2026
    r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",  # 14/10/2026
    r"\b\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?",  # 10:30 AM
    r"\+?\d[\d\s()-]{7,}\d",  # phone numbers (and dosing patterns like 1 - 0 - 1)
    r"\b\d+(?:[.,]\d+)*\s*(?:%|(?:mg|mcg|µg|gm|g|ml|iu|units?|tablets?|tabs?|capsules?|caps?|puffs?|drops?)\b)",
    r"\d+(?:[.,]\d+)*",  # any other number
)
_TOKEN_PREFIX = "ZQX"  # noqa: S105 — placeholder marker, not a secret
_TOKEN = re.compile(_TOKEN_PREFIX + r"[A-Z]{2}")
_DIGITS = re.compile(r"\d+")  # Unicode digits too: a Devanagari numeral in the output fails verification
_LETTERS = re.compile(r"[^\W\d_]")

_CACHE_MAX = 2048
_CACHE: dict[tuple[str, str, tuple[str, ...]], str] = {}
# Verified translations also persist on disk so restarts/redeploys don't re-spend the free engines' quota.
# ponytail: one SQLite file beside the private document store; move to a DB table if multi-host.
_DISK_CACHE_NAME = ".translation_cache.sqlite3"
_FREE_BATCH_CHARS = 4500  # free Google endpoint limit per request is ~5000 chars


def _disk() -> sqlite3.Connection:
    root = get_settings().storage_path
    root.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(root / _DISK_CACHE_NAME)
    con.execute("CREATE TABLE IF NOT EXISTS t (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
    return con


def _cache_get(key: tuple[str, str, tuple[str, ...]]) -> str | None:
    if (hit := _CACHE.get(key)) is not None:
        return hit
    try:
        with _disk() as con:
            row = con.execute("SELECT v FROM t WHERE k = ?", (json.dumps(key),)).fetchone()
    except sqlite3.Error:
        return None
    if row:
        _CACHE[key] = row[0]
    return row[0] if row else None


def _cache_put(key: tuple[str, str, tuple[str, ...]], value: str) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = value
    try:
        with _disk() as con:
            con.execute("INSERT OR REPLACE INTO t (k, v) VALUES (?, ?)", (json.dumps(key), value))
    except sqlite3.Error:
        logger.warning("Translation disk cache unavailable")


def clear_cache() -> None:
    """Drop both cache layers (tests)."""
    _CACHE.clear()
    try:
        with _disk() as con:
            con.execute("DELETE FROM t")
    except sqlite3.Error:
        pass

Engine = Callable[[list[str], Language], Awaitable[list[str | None]]]


def _token(i: int) -> str:
    return f"{_TOKEN_PREFIX}{chr(65 + i // 26)}{chr(65 + i % 26)}"


def mask(text: str, protected_terms: Sequence[str] = ()) -> tuple[str, dict[str, str]]:
    """Replace protected spans with placeholder tokens. Returns (masked_text, token → original)."""
    terms = sorted({t for t in protected_terms if t.strip()}, key=len, reverse=True)
    rx = re.compile("|".join([*(rf"(?<!\w){re.escape(t)}(?!\w)" for t in terms), *_PROTECTED]), re.I)
    mapping: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        tok = _token(len(mapping))
        mapping[tok] = m.group()
        return tok

    masked = rx.sub(repl, text)
    if len(mapping) > 26 * 26:
        raise ValueError("too many protected spans")
    return masked, mapping


def unmask(translated: str | None, source: str, mapping: dict[str, str]) -> str | None:
    """Restore placeholders and verify nothing protected was lost or altered. None on any doubt."""
    if not translated or not translated.strip() or "UNTRANSLATABLE" in translated:
        return None
    if any(translated.count(tok) != 1 for tok in mapping):
        return None
    out = translated
    for tok, original in mapping.items():
        out = out.replace(tok, original)
    if _TOKEN_PREFIX in out or sorted(_DIGITS.findall(out)) != sorted(_DIGITS.findall(source)):
        return None
    return out.strip()


async def _google_v2(texts: list[str], lang: Language) -> list[str | None]:
    key = get_settings().google_translate_api_key
    async with httpx.AsyncClient(timeout=TOTAL_TIMEOUT_S) as client:
        r = await client.post(
            GOOGLE_TRANSLATE_API_URL,
            json={"q": texts, "target": lang.value, "source": "en", "format": "text"},
            headers={"X-goog-api-key": key},  # header, never the URL: keys must not end up in access logs
        )
        r.raise_for_status()
        items = r.json()["data"]["translations"]
    if len(items) != len(texts):
        raise ValueError("Google v2 returned a different number of items")
    return [html.unescape(i.get("translatedText") or "") or None for i in items]


async def _llm(texts: list[str], lang: Language) -> list[str | None]:
    provider = get_inference_provider()
    system = load_prompt("translation_v1").replace("{{LANGUAGE}}", LANGUAGE_NAMES[lang])
    outs = await asyncio.gather(*(provider.generate_text(system, t) for t in texts), return_exceptions=True)
    return [o if isinstance(o, str) else None for o in outs]


async def _deep_translator(texts: list[str], lang: Language) -> list[str | None]:
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source="en", target=lang.value)
    # One request per ~4.5k chars instead of one per item: per-item bursts trip the free endpoint's
    # 5 requests/second limit and get the IP blocked for hours.
    chunks: list[list[str]] = [[]]
    for t in texts:
        t = t.replace("\n", " ")
        if chunks[-1] and sum(len(x) + 1 for x in chunks[-1]) + len(t) > _FREE_BATCH_CHARS:
            chunks.append([])
        chunks[-1].append(t)

    def run() -> list[str | None]:
        out: list[str | None] = []
        for chunk in chunks:
            lines = (translator.translate("\n".join(chunk)) or "").split("\n")
            out.extend(lines if len(lines) == len(chunk) else [None] * len(chunk))
        return out

    # ponytail: blocking client in a worker thread; on timeout the thread is abandoned, not killed.
    return await asyncio.to_thread(run)


async def _mymemory(texts: list[str], lang: Language) -> list[str | None]:
    """Last resort when the free Google endpoint rate-limits this IP (common on shared networks)."""
    from deep_translator import MyMemoryTranslator

    def run() -> list[str | None]:
        # Sequential, and stop at the first refusal: parallel bursts burn the daily quota (~5k chars/IP).
        out: list[str | None] = []
        for text in texts:
            try:
                result = MyMemoryTranslator(source="en-GB", target=f"{lang.value}-IN").translate(text)
            except Exception as exc:  # noqa: BLE001 — quota/rate limit/network: give up on the rest
                skipped = len(texts) - len(out)
                logger.warning("MyMemory refused (%s); skipping %d items", type(exc).__name__, skipped)
                break
            if not result or "MYMEMORY WARNING" in result.upper():  # quota notice returned as "translation"
                break
            out.append(result)
        return out + [None] * (len(texts) - len(out))

    return await asyncio.to_thread(run)


def _engines() -> list[tuple[str, Engine]]:
    settings = get_settings()
    engines: list[tuple[str, Engine]] = []
    if settings.google_translate_api_key:
        engines.append(("google_v2", _google_v2))
    if settings.inference_provider != "rule_based":
        engines.append(("llm", _llm))
    engines.append(("deep_translator", _deep_translator))
    engines.append(("mymemory", _mymemory))
    return engines


async def translate_texts(
    texts: list[str], target_lang: Language, protected_terms: Sequence[str] = ()
) -> list[str | None]:
    """Translate English patient text. Item → None when no engine produced a verified translation."""
    lang = Language(target_lang)
    if lang == Language.EN:
        return list(texts)
    protected = tuple(sorted({t.strip() for t in protected_terms if t and t.strip()}))
    results: list[str | None] = [None] * len(texts)
    pending: dict[int, tuple[str, dict[str, str]]] = {}
    for i, text in enumerate(texts):
        if (cached := _cache_get((text, lang.value, protected))) is not None:
            results[i] = cached
            continue
        try:
            masked, mapping = mask(text, protected)
        except ValueError:
            continue
        if not _LETTERS.search(_TOKEN.sub("", masked)):
            results[i] = text  # nothing translatable (only names/numbers/dates)
        else:
            pending[i] = (masked, mapping)

    loop = asyncio.get_running_loop()
    deadline = loop.time() + TOTAL_TIMEOUT_S
    for name, engine in _engines():
        remaining = deadline - loop.time()
        if not pending or remaining <= 0:
            break
        idx = list(pending)
        try:
            outs = await asyncio.wait_for(engine([pending[i][0] for i in idx], lang), remaining)
        except Exception as exc:  # noqa: BLE001 — engine failure must never reach the caller
            logger.warning(
                "Translation engine %s failed (%s) for %d items", name, type(exc).__name__, len(idx)
            )
            continue
        accepted = 0
        for i, out in zip(idx, outs, strict=False):
            final = unmask(out, texts[i], pending[i][1])
            if final is None:
                continue
            results[i] = final
            del pending[i]
            accepted += 1
            _cache_put((texts[i], lang.value, protected), final)
        logger.info(
            "Translation engine %s accepted %d/%d items (lang=%s)", name, accepted, len(idx), lang.value
        )
    if pending:
        logger.info("Translation unavailable for %d/%d items (lang=%s)", len(pending), len(texts), lang.value)
    return results
