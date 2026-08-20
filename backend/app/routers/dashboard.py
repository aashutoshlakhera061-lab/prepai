from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=schemas.DashboardOut)
def get_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    attempts = (
        db.query(models.MockTestAttempt)
        .filter(models.MockTestAttempt.user_id == current_user.id)
        .order_by(models.MockTestAttempt.created_at.asc())
        .all()
    )

    topic_scores_all = defaultdict(list)
    accuracy_trend = []
    for a in attempts:
        accuracy_trend.append(a.score_pct)
        for topic, pct in (a.topic_breakdown or {}).items():
            topic_scores_all[topic].append(pct)

    topic_scores = {t: round(sum(v) / len(v), 1) for t, v in topic_scores_all.items()}

    flashcards_reviewed = (
        db.query(models.Flashcard)
        .join(models.Document)
        .filter(models.Document.owner_id == current_user.id, models.Flashcard.times_reviewed > 0)
        .count()
    )

    # Interview readiness: a simple weighted blend. Replace with a trained
    # model (see ML notes in README) once you have enough labeled outcome data.
    avg_mock_score = sum(accuracy_trend) / len(accuracy_trend) if accuracy_trend else 0
    avg_retention = 0
    cards = db.query(models.Flashcard).join(models.Document).filter(
        models.Document.owner_id == current_user.id
    ).all()
    if cards:
        avg_retention = sum(c.retention for c in cards) / len(cards) * 100

    readiness = round(0.6 * avg_mock_score + 0.4 * avg_retention, 1) if (accuracy_trend or cards) else 0.0

    top_priority = min(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else None

    return schemas.DashboardOut(
        interview_readiness=readiness,
        topic_scores=topic_scores,
        mock_tests_taken=len(attempts),
        flashcards_reviewed=flashcards_reviewed,
        top_priority_topic=top_priority,
        accuracy_trend=accuracy_trend,
    )
