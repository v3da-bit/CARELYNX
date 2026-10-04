from sqlalchemy.orm import Session

from app.models import Case, Document, Evidence, Fact, Patient
from app.models.enums import FactStatus, FactType


def test_models_roundtrip(db: Session) -> None:
    p = Patient()
    db.add(p)
    db.flush()
    c = Case(patient_id=p.id)
    db.add(c)
    db.flush()
    d = Document(case_id=c.id, filename="a.pdf", mime_type="application/pdf", storage_key="k")
    db.add(d)
    db.flush()
    f = Fact(
        case_id=c.id,
        fact_type=FactType.FOLLOW_UP,
        value={"date": "2026-10-14"},
        status=FactStatus.VERIFIED,
        confidence=0.95,
    )
    f.evidence.append(Evidence(document_id=d.id, page_number=1, snippet="Follow-up on 14 Oct 2026"))
    db.add(f)
    db.commit()

    got = db.get(Fact, f.id)
    assert got is not None
    assert got.status is FactStatus.VERIFIED
    assert got.value == {"date": "2026-10-14"}
    assert got.confidence == 0.95
    assert got.evidence[0].page_number == 1
