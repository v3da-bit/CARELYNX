import asyncio
import json
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.entities import Patient, Case, Fact
from app.models.enums import FactType, FactStatus
from app.services.translation import (
    GOOGLE_TRANSLATE_API_URL,
    SUPPORTED_LANGUAGES,
    translate_with_google_v2,
    translate_facts,
    auto_translate_on_summary_created,
    clear_translation_cache,
)


@pytest.fixture(autouse=True)
def reset_cache():
    clear_translation_cache()
    yield
    clear_translation_cache()


def test_supported_languages():
    expected = {"en", "hi", "gu", "mr", "ta", "te"}
    assert set(SUPPORTED_LANGUAGES.keys()) == expected


def test_translate_with_google_v2_success():
    texts = ["Avoid heavy lifting", "Patient's follow-up", "Take with food"]
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "translations": [
                {"translatedText": "वजनदार चीजें उठाने से बचें"},
                {"translatedText": "Patient&#39;s फॉलो-अप"},  # Test HTML unescape
                {"translatedText": "भोजन के साथ लें"},
            ]
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        results = asyncio.run(
            translate_with_google_v2(
                texts=texts,
                target_lang="hi",
                api_key="test-api-key-12345",
            )
        )

        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert GOOGLE_TRANSLATE_API_URL in call_args[0]
        assert call_kwargs["json"]["q"] == texts
        assert call_kwargs["json"]["target"] == "hi"
        assert call_kwargs["json"]["source"] == "en"
        assert call_kwargs["json"]["format"] == "text"

        assert results[0] == "वजनदार चीजें उठाने से बचें"
        # Verify HTML entity decoding: &#39; -> '
        assert results[1] == "Patient's फॉलो-अप"
        assert results[2] == "भोजन के साथ लें"


def test_translate_with_google_v2_missing_key():
    with patch("app.services.translation.get_settings") as mock_settings:
        mock_settings.return_value.google_translate_api_key = ""
        with patch.dict("os.environ", {"GOOGLE_TRANSLATE_API_KEY": ""}, clear=False):
            with pytest.raises(ValueError, match="Google Translate API key not configured"):
                asyncio.run(translate_with_google_v2(["Hello"], target_lang="hi", api_key=""))


def test_translate_facts_english_direct(db: Session):
    patient = Patient(id=uuid.uuid4())
    db.add(patient)
    db.flush()
    case_id = uuid.uuid4()
    c = Case(id=case_id, patient_id=patient.id)
    db.add(c)
    db.flush()

    fact = Fact(
        case_id=case_id,
        fact_type=FactType.MEDICATION,
        value={"name": "Aspirin", "dose": "81mg", "instruction": "Take with food"},
        status=FactStatus.VERIFIED,
    )
    db.add(fact)
    db.commit()

    res = asyncio.run(translate_facts(db, str(case_id), "en"))
    assert res["language"] == "en"
    assert len(res["facts"]) == 1
    assert res["facts"][0]["translated_value"]["name"] == "Aspirin"
    assert res["facts"][0]["translated_value"]["dose"] == "81mg"


def test_translate_facts_with_google_v2_and_cache(db: Session):
    patient = Patient(id=uuid.uuid4())
    db.add(patient)
    db.flush()
    case_id = uuid.uuid4()
    c = Case(id=case_id, patient_id=patient.id)
    db.add(c)
    db.flush()

    fact1 = Fact(
        case_id=case_id,
        fact_type=FactType.INSTRUCTION,
        value={"instruction": "Avoid heavy lifting", "raw_text": "Avoid heavy lifting"},
        status=FactStatus.VERIFIED,
    )
    fact2 = Fact(
        case_id=case_id,
        fact_type=FactType.FOLLOW_UP,
        value={"department": "Cardiology", "date": "2026-10-14"},
        status=FactStatus.VERIFIED,
    )
    db.add_all([fact1, fact2])
    db.commit()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "translations": [
                {"translatedText": "वजनदार चीजें उठाने से बचें"},
                {"translatedText": "वजनदार चीजें उठाने से बचें"},
                {"translatedText": "कार्डियोलॉजी"},
            ]
        }
    }

    with patch("app.services.translation.get_settings") as mock_settings:
        mock_settings.return_value.google_translate_api_key = "mock-test-key-safe"
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # First call uses Google Translate v2
            res1 = asyncio.run(translate_facts(db, str(case_id), "hi"))
            assert res1["language"] == "hi"
            assert res1.get("provider") == "google_translate_v2"
            assert len(res1["facts"]) == 2

            # Find translated care plan and follow up
            care_fact = next(f for f in res1["facts"] if f["id"] == str(fact1.id))
            assert care_fact["translated_value"]["instruction"] == "वजनदार चीजें उठाने से बचें"

            follow_fact = next(f for f in res1["facts"] if f["id"] == str(fact2.id))
            assert follow_fact["translated_value"]["department"] == "कार्डियोलॉजी"
            assert follow_fact["translated_value"]["date"] == "2026-10-14"  # Preserved verbatim!

            # Second call should hit memory cache without re-POSTing
            res2 = asyncio.run(translate_facts(db, str(case_id), "hi"))
            assert res2 == res1
            assert mock_post.call_count == 1


def test_auto_translate_on_summary_created(db: Session):
    patient = Patient(id=uuid.uuid4())
    db.add(patient)
    db.flush()
    case_id = uuid.uuid4()
    c = Case(id=case_id, patient_id=patient.id)
    db.add(c)
    db.flush()

    fact = Fact(
        case_id=case_id,
        fact_type=FactType.INSTRUCTION,
        value={"instruction": "Drink plenty of water"},
        status=FactStatus.VERIFIED,
    )
    db.add(fact)
    db.commit()

    with patch("app.services.translation.get_settings") as mock_settings:
        mock_settings.return_value.google_translate_api_key = "mock-test-key-safe"
        with patch("app.services.translation.translate_facts", new_callable=AsyncMock) as mock_translate:
            asyncio.run(auto_translate_on_summary_created(db, str(case_id), ["hi", "gu", "mr", "ta", "te"]))
            assert mock_translate.call_count == 5
