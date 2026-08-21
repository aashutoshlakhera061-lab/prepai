from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.services import llm_service

router = APIRouter(prefix="/summary", tags=["summary"])

MODE_PROMPTS = {
    "quick": "Write a QUICK 5-minute revision summary. Bullet points only, hit the core concepts, skip minor details.",
    "detailed": "Write a DETAILED, concept-by-concept explanation suitable for deep study. Use headings per concept.",
    "interview": "Write an INTERVIEW-FOCUSED summary: only the things that are actually likely to be asked in a technical interview, phrased as 'what an interviewer probes here'.",
    "cheatsheet": "Write a ONE-PAGE LAST-MINUTE cheat sheet: terse bullet points, formulas/definitions only, no prose.",
}


def _get_document_text(db: Session, document_id: int, owner_id: int) -> str:
    doc = db.query(models.Document).filter(
        models.Document.id == document_id, models.Document.owner_id == owner_id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    chunks = sorted(doc.chunks, key=lambda c: c.order_index)
    # Cap total context sent to the LLM to keep costs/latency sane.
    text = "\n\n".join(c.text for c in chunks)
    return text[:8000]


@router.post("/", response_model=schemas.SummaryResponse)
def generate_summary(payload: schemas.SummaryRequest, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    if payload.mode not in MODE_PROMPTS:
        raise HTTPException(400, f"mode must be one of {list(MODE_PROMPTS.keys())}")

    material = _get_document_text(db, payload.document_id, current_user.id)
    system = ("You are PrepAI's study-material summarizer. You ONLY use the material provided — "
               "never invent facts not present in it. " + MODE_PROMPTS[payload.mode])
    content = llm_service.generate_text(system=system, user_prompt=material, max_tokens=1800)
    return schemas.SummaryResponse(mode=payload.mode, content=content)
