from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.chat import ChatMessage, ChatRole
from src.models.cycle import Cycle
from src.models.user import User
from src.schemas.chat import ChatHistory, ChatMessageCreate, ChatResponse
from src.services.claude_service import MEDICAL_DISCLAIMER, get_chat_response
from src.services.phase_detector import cycle_day, detect_phase

router = APIRouter(prefix="/chat", tags=["chat"])

_MAX_HISTORY_MESSAGES = 20


def _build_context(db: Session, user: User) -> dict:
    stmt = (
        select(Cycle)
        .where(Cycle.user_id == user.id, Cycle.end_date.is_(None))
        .order_by(Cycle.start_date.desc())
    )
    cycle = db.execute(stmt).scalars().first()
    if cycle is None:
        return {"has_active_cycle": False, "cycle_goal": user.cycle_goal, "language": user.language}

    today = date.today()
    return {
        "has_active_cycle": True,
        "current_phase": detect_phase(cycle.start_date, today, user.average_cycle_length),
        "current_cycle_day": cycle_day(cycle.start_date, today),
        "cycle_goal": user.cycle_goal,
        "language": user.language,
        "gynecological_profile": user.gynecological_profile,
    }


@router.post("/", response_model=ChatResponse)
def send_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    conversation_history: list[dict] = []
    if payload.persist:
        history_stmt = (
            select(ChatMessage)
            .where(ChatMessage.user_id == current_user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(_MAX_HISTORY_MESSAGES)
        )
        recent = list(reversed(db.execute(history_stmt).scalars().all()))
        conversation_history = [{"role": m.role.value, "content": m.content} for m in recent]

    context = _build_context(db, current_user)

    try:
        reply = get_chat_response(payload.message, conversation_history, context)
    except Exception:
        reply = (
            "I'm having trouble connecting right now, so I can't give you a personalized reply. "
            "Please try again in a moment."
        )

    if payload.persist:
        user_message = ChatMessage(user_id=current_user.id, role=ChatRole.USER, content=payload.message)
        assistant_message = ChatMessage(user_id=current_user.id, role=ChatRole.ASSISTANT, content=reply)
        db.add(user_message)
        db.add(assistant_message)
        db.commit()

    return ChatResponse(reply=reply, disclaimer=MEDICAL_DISCLAIMER)


@router.get("/history", response_model=ChatHistory)
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistory:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = list(db.execute(stmt).scalars().all())
    return ChatHistory(messages=messages)
