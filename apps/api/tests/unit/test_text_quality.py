from app.safety.text_quality import line_quality, page_quality, suspicious_tokens


def test_detects_ocr_confusables() -> None:
    sus = suspicious_tokens("1. Metf0rmin 5OO mg - 1 tab - tw?ce dai1y - 3O days, on 1? Oct")
    assert {"Metf0rmin", "5OO", "tw?ce", "dai1y", "3O", "1?"} <= set(sus)


def test_clean_text_not_flagged() -> None:
    line = "2. Amlodipine 5 mg - 1 tablet - once daily - 30 days. Follow-up on 14 Oct 2026 at 10:30 AM (OPD)."
    assert suspicious_tokens(line) == []
    assert line_quality(line).score == 1.0


def test_page_quality_scores() -> None:
    assert page_quality(None).score == 0.0
    assert page_quality("").flags == ["NO_TEXT"]
    clean = page_quality("Rest at home for seven days and drink plenty of fluids every day.")
    assert clean.score == 1.0
    bad = page_quality("Metf0rmin 5OO mg tw?ce dai1y for 3O days")
    assert bad.score < 0.85
