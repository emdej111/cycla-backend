"""GDPR data subject rights: export and erasure. Kept as its own router
(rather than folded into auth.py) since these are account-lifecycle
operations distinct from authentication.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.chat import ChatMessage
from src.models.checkin import DailyCheckin
from src.models.cycle import Cycle
from src.models.document import MedicalDocument
from src.models.insight import Insight
from src.models.user import User

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/export")
def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    cycles = db.execute(select(Cycle).where(Cycle.user_id == current_user.id)).scalars().all()
    checkins = db.execute(
        select(DailyCheckin).where(DailyCheckin.user_id == current_user.id)
    ).scalars().all()
    insights = db.execute(select(Insight).where(Insight.user_id == current_user.id)).scalars().all()
    documents = db.execute(
        select(MedicalDocument).where(MedicalDocument.user_id == current_user.id)
    ).scalars().all()
    chat_messages = db.execute(
        select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    ).scalars().all()

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "age": current_user.age,
            "created_at": current_user.created_at.isoformat(),
            "gynecological_profile": current_user.gynecological_profile,
            "cycle_goal": current_user.cycle_goal,
            "language": current_user.language,
            "average_cycle_length": current_user.average_cycle_length,
            "tracked_cycles_count": current_user.tracked_cycles_count,
        },
        "cycles": [
            {
                "id": c.id,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "cycle_length": c.cycle_length,
                "phase": c.phase,
                "predicted_ovulation_date": c.predicted_ovulation_date.isoformat()
                if c.predicted_ovulation_date
                else None,
                "notes": c.notes,
            }
            for c in cycles
        ],
        "checkins": [
            {column.name: getattr(c, column.name) for column in DailyCheckin.__table__.columns}
            for c in checkins
        ],
        "insights": [
            {
                "id": i.id,
                "date": i.date.isoformat(),
                "type": i.type,
                "content": i.content,
                "is_personalized": i.is_personalized,
                "scientific_sources": i.scientific_sources,
            }
            for i in insights
        ],
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "upload_date": d.upload_date.isoformat(),
                "document_type": d.document_type,
                "claude_analysis": d.claude_analysis,
                "affects_personalization": d.affects_personalization,
            }
            for d in documents
        ],
        "chat_messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in chat_messages
        ],
    }


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    # Cascades to cycles, checkins, insights, documents, chat_messages via
    # relationship(cascade="all, delete-orphan") on User.
    db.delete(current_user)
    db.commit()
