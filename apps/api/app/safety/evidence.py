"""Verbatim evidence matcher (ARCHITECTURE §3.5, SAFETY.md §2, FR-008).

The inference provider is never trusted to assert that a quote exists on a page.
Application code must confirm the snippet is a literal substring of extracted page text
before a fact can be treated as verified.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceMatch:
    verified: bool
    char_start: int | None
    char_end: int | None
    reason: str
    page_number: int | None = None


def match_verbatim(page_text: str | None, snippet: str | None, *, page_number: int | None = None) -> EvidenceMatch:
    """Return whether `snippet` appears verbatim in `page_text`.

    Matching is exact (no LLM paraphrase, no fuzzy edit distance). Leading/trailing
    whitespace on the snippet is stripped so provider padding cannot invent a miss,
    but interior characters must match the source page exactly.
    """
    if page_text is None or not str(page_text).strip():
        return EvidenceMatch(False, None, None, "Source page has no extractable text", page_number)

    quote = (snippet or "").strip()
    if len(quote) < 3:
        return EvidenceMatch(False, None, None, "Evidence snippet is missing or too short", page_number)

    index = page_text.find(quote)
    if index < 0:
        return EvidenceMatch(
            False, None, None, "Snippet does not appear verbatim on the cited page", page_number
        )

    return EvidenceMatch(True, index, index + len(quote), "Verbatim substring match", page_number)


def match_verbatim_across_pages(
    pages: dict[int, str | None],
    snippet: str | None,
    cited_page: int,
) -> EvidenceMatch:
    """Confirm a snippet exists verbatim. Prefer the cited page; relocate if the quote lives elsewhere.

    Relocating the page number is not a clinical guess — it only records the page that
    actually contains the exact substring.
    """
    cited = match_verbatim(pages.get(cited_page), snippet, page_number=cited_page)
    if cited.verified:
        return cited
    for page_number, text in pages.items():
        if page_number == cited_page:
            continue
        relocated = match_verbatim(text, snippet, page_number=page_number)
        if relocated.verified:
            return EvidenceMatch(
                True,
                relocated.char_start,
                relocated.char_end,
                "Verbatim match on a different page than the provider cited",
                page_number,
            )
    return cited
