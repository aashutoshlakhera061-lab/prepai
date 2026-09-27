import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, utcnow
from app import models, schemas, auth
from app.services import llm_service

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

SYSTEM_PROMPT = """You generate flashcards strictly from the given study material.
Return a JSON array of objects: [{"question": "...", "answer": "...", "difficulty": "easy|medium|hard"}]
Cover the most important concepts. Answers should be concise (1-3 sentences)."""


@router.post("/generate", response_model=list[schemas.FlashcardOut])
def generate_flashcards(payload: schemas.FlashcardGenerateRequest, db: Session = Depends(get_db),
                         current_user: models.User = Depends(auth.get_current_user)):
    doc = db.query(models.Document).filter(
        models.Document.id == payload.document_id, models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    material = "\n\n".join(c.text for c in sorted(doc.chunks, key=lambda c: c.order_index))[:8000]
    user_prompt = f"Generate exactly {payload.count} flashcards from this material:\n\n{material}"
    cards = llm_service.generate_json(SYSTEM_PROMPT, user_prompt, max_tokens=2500)

    created = []
    for card in cards:
        fc = models.Flashcard(
            document_id=doc.id,
            question=card["question"],
            answer=card["answer"],
            difficulty=card.get("difficulty", "medium"),
            retention=0.5,
            next_due=utcnow(),
        )
        db.add(fc)
        created.append(fc)
    db.commit()
    for fc in created:
        db.refresh(fc)
    return created


@router.get("/due", response_model=list[schemas.FlashcardOut])
def get_due_flashcards(document_id: int, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    now = utcnow()
    cards = (
        db.query(models.Flashcard)
        .join(models.Document)
        .filter(models.Document.owner_id == current_user.id, models.Flashcard.document_id == document_id,
                models.Flashcard.next_due <= now)
        .order_by(models.Flashcard.retention.asc())
        .all()
    )
    return cards


@router.post("/review")
def review_flashcard(payload: schemas.FlashcardReview, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    """Simple SM-2-inspired spaced repetition: adjusts retention estimate and
    schedules next review interval based on it. Swap for a real SM-2/FSRS
    implementation if you want closer-to-Anki scheduling."""
    fc = db.query(models.Flashcard).join(models.Document).filter(
        models.Flashcard.id == payload.flashcard_id, models.Document.owner_id == current_user.id
    ).first()
    if not fc:
        raise HTTPException(404, "Flashcard not found")

    if payload.got_it_right:
        fc.retention = min(1.0, fc.retention + 0.15)
    else:
        fc.retention = max(0.0, fc.retention - 0.25)

    fc.times_reviewed += 1
    fc.last_reviewed = utcnow()
    # Higher retention -> longer interval before it's due again.
    interval_days = max(1, round(fc.retention * 14))
    fc.next_due = utcnow() + datetime.timedelta(days=interval_days)

    db.commit()
    return {"ok": True, "new_retention": fc.retention, "next_due": fc.next_due}
