from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.services import llm_service, rag

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """You are PrepAI's study assistant. Answer the user's question using ONLY the
provided material context. If the material doesn't cover it, say so plainly rather than guessing.
Be concise and exam/interview-focused. Cite page numbers from the context when relevant.
Format any math using $...$ for inline expressions and $$...$$ for standalone equations
(not \\( \\) or \\[ \\])."""


@router.post("/", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db),
         current_user: models.User = Depends(auth.get_current_user)):
    doc = db.query(models.Document).filter(
        models.Document.id == payload.document_id, models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    all_chunks = [{"id": c.id, "text": c.text, "page": c.page} for c in doc.chunks]
    relevant = rag.retrieve_relevant_chunks(payload.message, all_chunks, top_k=6)
    context = rag.build_context(relevant)

    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in payload.history[-6:])
    user_prompt = f"CONTEXT:\n{context}\n\nCONVERSATION SO FAR:\n{history_text}\n\nUSER QUESTION:\n{payload.message}"

    reply = llm_service.generate_text(system=SYSTEM_PROMPT, user_prompt=user_prompt, max_tokens=1000)
    sources = [f"Page {c['page']}" for c in relevant]
    return schemas.ChatResponse(reply=reply, sources=sources)
