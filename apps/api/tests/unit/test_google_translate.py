"""translate_texts: masking, verification, engine order. No network — every engine is mocked."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import httpx
import pytest

from app.models.enums import Language
from app.services import translation
from app.services.translation import mask, translate_texts, unmask

SRC = "Aspirin 75 mg once daily after lunch from 14 Oct 2026 at 10:30 AM, call 022-2345-6789"


@pytest.fixture(autouse=True)
def _clean_cache():
    translation.clear_cache()
    yield
    translation.clear_cache()


def _fake_engine(fn, calls=None):
    """An engine that 'translates' masked text with `fn` (and records calls)."""

    async def engine(texts, lang):
        if calls is not None:
            calls.append(list(texts))
        return [fn(t) for t in texts]

    return engine


def _hindi(t: str) -> str:
    return "अनुवाद: " + t  # keeps every placeholder intact


def _run(texts, lang, engines, protected=()):
    with patch.object(translation, "_engines", lambda: engines):
        return asyncio.run(translate_texts(texts, lang, protected_terms=protected))


def test_mask_round_trip_protects_drugs_doses_dates_times_phones_numbers() -> None:
    masked, mapping = mask(SRC, ["Aspirin"])
    for protected in ("Aspirin", "75 mg", "14 Oct 2026", "10:30 AM", "022-2345-6789"):
        assert protected not in masked
        assert protected in mapping.values()
    assert not any(ch.isdigit() for ch in masked)
    assert unmask(masked, SRC, mapping) == SRC


@pytest.mark.parametrize(
    "src", ["Take 500mg twice", "Dose 10 ml", "Review on 14/10/2026", "Next visit 2026-10-14", "Oct 14, 2026"]
)
def test_mask_formats(src: str) -> None:
    masked, mapping = mask(src)
    assert not any(ch.isdigit() for ch in masked)
    assert unmask(masked, src, mapping) == src


def test_dropped_or_duplicated_placeholder_is_rejected() -> None:
    masked, mapping = mask(SRC, ["Aspirin"])
    first = next(iter(mapping))
    assert unmask(masked.replace(first, ""), SRC, mapping) is None
    assert unmask(masked + " " + first, SRC, mapping) is None


def test_altered_or_added_number_is_rejected() -> None:
    masked, mapping = mask("Take 1 tablet for 5 days")
    assert unmask(masked + " 2", "Take 1 tablet for 5 days", mapping) is None
    assert unmask(masked + " ३", "Take 1 tablet for 5 days", mapping) is None  # Devanagari digit counts


def test_abstention_is_rejected() -> None:
    assert unmask("UNTRANSLATABLE", "Rest at home", {}) is None


def test_english_passthrough_never_calls_an_engine() -> None:
    calls: list = []
    out = _run(["Rest at home", "x"], Language.EN, [("e", _fake_engine(_hindi, calls))])
    assert out == ["Rest at home", "x"] and calls == []


@pytest.mark.parametrize("lang", [Language.HI, Language.GU, Language.MR, Language.TA, Language.TE])
def test_all_supported_languages_translate(lang: Language) -> None:
    out = _run([SRC], lang, [("e", _fake_engine(_hindi))], protected=["Aspirin"])
    assert out == ["अनुवाद: " + SRC]


def test_engine_fallback_order_and_per_item_retry() -> None:
    first_calls: list = []
    second_calls: list = []

    def drop_numbers_in_second(t: str) -> str:  # first engine corrupts item 2 only
        return t.replace(next(iter(mask("Take 2 tablets")[1])), "") if t.startswith("Take") else _hindi(t)

    out = _run(
        ["Rest at home", "Take 2 tablets"],
        Language.HI,
        [
            ("first", _fake_engine(drop_numbers_in_second, first_calls)),
            ("second", _fake_engine(_hindi, second_calls)),
        ],
    )
    assert out == ["अनुवाद: Rest at home", "अनुवाद: Take 2 tablets"]
    assert len(first_calls[0]) == 2 and len(second_calls[0]) == 1  # only the rejected item retried


def test_engine_exceptions_and_timeouts_never_raise() -> None:
    async def boom(texts, lang):
        raise httpx.ConnectError("offline")

    async def slow(texts, lang):
        await asyncio.sleep(5)
        return texts

    with patch.object(translation, "TOTAL_TIMEOUT_S", 0.2):
        out = _run(["Rest at home"], Language.GU, [("boom", boom), ("slow", slow)])
    assert out == [None]


def test_results_are_cached_per_text_lang_and_terms() -> None:
    calls: list = []
    engines = [("e", _fake_engine(_hindi, calls))]
    _run(["Rest at home"], Language.HI, engines)
    _run(["Rest at home"], Language.HI, engines)
    _run(["Rest at home"], Language.GU, engines)
    assert len(calls) == 2


def test_engine_selection_follows_configuration() -> None:
    class S:
        google_translate_api_key = ""
        inference_provider = "rule_based"

    with patch.object(translation, "get_settings", lambda: S):
        assert [n for n, _ in translation._engines()] == ["deep_translator", "mymemory"]
        S.google_translate_api_key, S.inference_provider = "k", "openai_compat"
        assert [n for n, _ in translation._engines()] == ["google_v2", "llm", "deep_translator", "mymemory"]


def test_google_v2_sends_key_in_header_not_url() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"], seen["key"] = str(request.url), request.headers.get("X-goog-api-key")
        body = json.loads(request.content)
        return httpx.Response(
            200, json={"data": {"translations": [{"translatedText": _hindi(q)} for q in body["q"]]}}
        )

    real_client = httpx.AsyncClient

    class S:
        google_translate_api_key = "secret-key"

    with (
        patch.object(translation, "get_settings", lambda: S),
        patch.object(
            translation.httpx,
            "AsyncClient",
            lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
        ),
    ):
        out = asyncio.run(translation._google_v2(["a &amp; b"], Language.HI))
    assert seen["key"] == "secret-key" and "secret-key" not in seen["url"]
    assert out == ["अनुवाद: a & b"]


def test_llm_engine_uses_versioned_prompt() -> None:
    seen: dict = {}

    class FakeProvider:
        async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
            seen["system"] = system_prompt
            return _hindi(user_prompt)

    with patch.object(translation, "get_inference_provider", lambda: FakeProvider()):
        out = asyncio.run(translation._llm(["Rest"], Language.TA))
    assert out == ["अनुवाद: Rest"]
    assert "Tamil" in seen["system"] and "Never change certainty" in seen["system"]


def test_free_google_sends_one_request_per_batch() -> None:
    calls: list[str] = []

    class FakeGoogle:
        def __init__(self, **_: object) -> None: ...

        def translate(self, text: str) -> str:
            calls.append(text)
            return "\n".join(f"HI:{line}" for line in text.split("\n"))

    with patch("deep_translator.GoogleTranslator", FakeGoogle):
        out = asyncio.run(translation._deep_translator([f"item {i}" for i in range(17)], Language.HI))
    assert len(calls) == 1  # not 17: per-item bursts get the IP rate-limited
    assert out == [f"HI:item {i}" for i in range(17)]


def test_free_google_line_mismatch_yields_none() -> None:
    class FakeGoogle:
        def __init__(self, **_: object) -> None: ...

        def translate(self, text: str) -> str:
            return "merged into one line"

    with patch("deep_translator.GoogleTranslator", FakeGoogle):
        out = asyncio.run(translation._deep_translator(["a", "b"], Language.HI))
    assert out == [None, None]


def test_mymemory_stops_at_quota_warning_and_never_returns_it() -> None:
    calls: list[str] = []

    class FakeMyMemory:
        def __init__(self, **_: object) -> None: ...

        def translate(self, text: str) -> str:
            calls.append(text)
            return "ठीक" if len(calls) == 1 else "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS"

    with patch("deep_translator.MyMemoryTranslator", FakeMyMemory):
        out = asyncio.run(translation._mymemory(["a", "b", "c", "d"], Language.HI))
    assert out == ["ठीक", None, None, None]
    assert len(calls) == 2  # stopped after the refusal instead of hammering the quota


def test_verified_translations_survive_a_restart() -> None:
    engine_calls: list[list[str]] = []
    engines = [("fake", _fake_engine(lambda t: f"HI {t}", engine_calls))]
    with patch.object(translation, "_engines", lambda: engines):
        first = asyncio.run(translate_texts(["Drink plenty of fluids"], Language.HI))
        translation._CACHE.clear()  # simulate a process restart: memory gone, disk kept
        second = asyncio.run(translate_texts(["Drink plenty of fluids"], Language.HI))
    assert first == second == ["HI Drink plenty of fluids"]
    assert len(engine_calls) == 1
