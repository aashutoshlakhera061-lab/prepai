from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/mistakes", tags=["mistakes"])


@router.get("/", response_model=list[schemas.MistakeOut])
def list_mistakes(topic: str | None = None, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    q = db.query(models.Mistake).filter(models.Mistake.user_id == current_user.id)
    if topic:
        q = q.filter(models.Mistake.topic == topic)
    return q.order_by(models.Mistake.created_at.desc()).all()
