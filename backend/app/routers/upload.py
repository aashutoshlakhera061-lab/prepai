import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.config import settings
from app.services import pdf_processor

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=schemas.DocumentOut)
def upload_document(
    file: UploadFile = File(...),
    subject: str = Form("General"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported in this MVP. "
                                  "Add .docx/.pptx parsing in pdf_processor.py to extend.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    save_path = os.path.join(settings.upload_dir, f"{current_user.id}_{file.filename}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = models.Document(owner_id=current_user.id, filename=file.filename, subject=subject)
    db.add(document)
    db.commit()
    db.refresh(document)

    pages = pdf_processor.extract_pages(save_path)
    if not pages:
        raise HTTPException(400, "Could not extract any text from this PDF (it may be scanned/image-only).")

    chunks = pdf_processor.chunk_text(pages)
    for c in chunks:
        db.add(models.Chunk(document_id=document.id, text=c["text"], page=c["page"], order_index=c["order_index"]))
    db.commit()

    return document


@router.get("/", response_model=list[schemas.DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Document).filter(models.Document.owner_id == current_user.id).all()


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    doc = db.query(models.Document).filter(
        models.Document.id == document_id, models.Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return {"ok": True}
