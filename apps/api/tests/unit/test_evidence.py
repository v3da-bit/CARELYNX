"""Verbatim evidence matcher tests (FR-008, SAFETY.md §2)."""

from app.safety.evidence import match_verbatim, match_verbatim_across_pages


def test_verbatim_substring_is_verified() -> None:
    page = "Discharge medications: Lisinopril 10mg PO daily (Morning)."
    match = match_verbatim(page, "Lisinopril 10mg PO daily")
    assert match.verified is True
    assert match.char_start == page.find("Lisinopril 10mg PO daily")
    assert match.char_end == match.char_start + len("Lisinopril 10mg PO daily")


def test_paraphrase_is_rejected() -> None:
    page = "Take Lisinopril 10mg by mouth every morning."
    match = match_verbatim(page, "The patient should continue ACE inhibitor therapy")
    assert match.verified is False
    assert "does not appear verbatim" in match.reason


def test_empty_page_cannot_verify() -> None:
    match = match_verbatim("   ", "Lisinopril 10mg")
    assert match.verified is False
    assert "no extractable text" in match.reason


def test_short_snippet_is_rejected() -> None:
    match = match_verbatim("Lisinopril 10mg PO daily", "Li")
    assert match.verified is False
    assert "too short" in match.reason


def test_relocates_verbatim_quote_to_actual_page() -> None:
    pages = {
        1: "Admission notes only.",
        2: "Follow up with Primary Care Physician on Oct 14, 2026.",
    }
    match = match_verbatim_across_pages(pages, "Primary Care Physician on Oct 14, 2026", cited_page=1)
    assert match.verified is True
    assert match.page_number == 2
