from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.services import llm_service

router = APIRouter(prefix="/mocktest", tags=["mocktest"])

SYSTEM_PROMPT = """You generate multiple-choice mock test questions STRICTLY from the given
study material — never invent facts outside it. Return a JSON array:
[{"question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0,
  "topic": "short topic label e.g. 'Multithreading'", "source": "e.g. Page 4"}]
Vary topics to cover the material broadly. Match the requested difficulty."""


@router.post("/generate", response_model=schemas.MockTestOut)
def generate_mock_test(payload: schemas.MockTestGenerateRequest, db: Session = Depends(get_db),
                        current_user: models.User = Depends(auth.get_current_user)):
    doc = db.query(models.Document).filter(
        models.Document.id == payload.document_id, models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Adaptive weighting: if the user has prior attempts on this document's mock
    # tests, bias question generation toward their weakest topics.
    past_tests = db.query(models.MockTest).filter(models.MockTest.document_id == doc.id).all()
    past_ids = [t.id for t in past_tests]
    weak_topics = []
    if past_ids:
        attempts = db.query(models.MockTestAttempt).filter(
            models.MockTestAttempt.user_id == current_user.id,
            models.MockTestAttempt.mock_test_id.in_(past_ids),
        ).all()
        topic_scores = defaultdict(list)
        for a in attempts:
            for topic, pct in (a.topic_breakdown or {}).items():
                topic_scores[topic].append(pct)
        weak_topics = sorted(
            ((t, sum(v) / len(v)) for t, v in topic_scores.items()), key=lambda x: x[1]
        )[:3]
        weak_topics = [t for t, _ in weak_topics]

    material = "\n\n".join(c.text for c in sorted(doc.chunks, key=lambda c: c.order_index))[:6000]
    focus_note = f"\n\nPrioritize extra questions on these weak topics if present in the material: {weak_topics}" if weak_topics else ""
    user_prompt = (
        f"Generate exactly {payload.num_questions} {payload.difficulty}-difficulty MCQs "
        f"from this material:{focus_note}\n\n{material}"
    )
    questions = llm_service.generate_json(SYSTEM_PROMPT, user_prompt, max_tokens=3200)

    mock_test = models.MockTest(
        document_id=doc.id, subject=doc.subject, difficulty=payload.difficulty, questions=questions
    )
    db.add(mock_test)
    db.commit()
    db.refresh(mock_test)
    return mock_test


@router.post("/submit", response_model=schemas.MockTestResult)
def submit_mock_test(payload: schemas.MockTestSubmit, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    test = db.query(models.MockTest).filter(models.MockTest.id == payload.mock_test_id).first()
    if not test:
        raise HTTPException(404, "Mock test not found")

    questions = test.questions
    if len(payload.answers) != len(questions):
        raise HTTPException(400, "Answers length must match number of questions")

    correct_count = 0
    topic_correct = defaultdict(lambda: [0, 0])  # topic -> [correct, total]
    mistakes_logged = 0

    for q, selected in zip(questions, payload.answers):
        topic = q.get("topic", "General")
        topic_correct[topic][1] += 1
        is_correct = selected == q.get("correct_index")
        if is_correct:
            correct_count += 1
            topic_correct[topic][0] += 1
        else:
            mistakes_logged += 1
            options = q.get("options", [])
            user_ans_text = options[selected] if 0 <= selected < len(options) else "No answer"
            correct_ans_text = options[q.get("correct_index", 0)] if options else ""
            db.add(models.Mistake(
                user_id=current_user.id,
                topic=topic,
                question=q.get("question", ""),
                user_answer=user_ans_text,
                correct_answer=correct_ans_text,
                category="conceptual",  # a follow-up LLM call could classify this more precisely
            ))

    score_pct = round(100 * correct_count / max(1, len(questions)), 1)
    topic_breakdown = {
        t: round(100 * c / max(1, tot), 1) for t, (c, tot) in topic_correct.items()
    }

    attempt = models.MockTestAttempt(
        user_id=current_user.id, mock_test_id=test.id, answers=payload.answers,
        score_pct=score_pct, topic_breakdown=topic_breakdown,
    )
    db.add(attempt)
    db.commit()

    return schemas.MockTestResult(score_pct=score_pct, topic_breakdown=topic_breakdown, mistakes_logged=mistakes_logged)
