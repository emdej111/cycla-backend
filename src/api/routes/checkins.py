from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.checkin import DailyCheckin
from src.models.cycle import Cycle
from src.models.user import User
from src.schemas.checkin import CheckinCreate, CheckinHistory, CheckinRead

router = APIRouter(prefix="/checkins", tags=["checkins"])


def _cycle_for_date(db: Session, user_id: int, target_date: date) -> Cycle | None:
    stmt = (
        select(Cycle)
        .where(
            Cycle.user_id == user_id,
            Cycle.start_date <= target_date,
            (Cycle.end_date.is_(None)) | (Cycle.end_date > target_date),
        )
        .order_by(Cycle.start_date.desc())
    )
    return db.execute(stmt).scalars().first()


@router.post("/", response_model=CheckinRead, status_code=status.HTTP_201_CREATED)
def create_checkin(
    payload: CheckinCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckinRead:
    existing = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id, DailyCheckin.date == payload.date)
        .first()
    )
    cycle = _cycle_for_date(db, current_user.id, payload.date)
    data = payload.model_dump()

    if existing is not None:
        for field, value in data.items():
            setattr(existing, field, value)
        existing.cycle_id = cycle.id if cycle else None
        checkin = existing
    else:
        checkin = DailyCheckin(user_id=current_user.id, cycle_id=cycle.id if cycle else None, **data)

    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return CheckinRead.model_validate(checkin)


@router.get("/history", response_model=CheckinHistory)
def get_checkin_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckinHistory:
    cutoff = date.today() - timedelta(days=90)
    stmt = (
        select(DailyCheckin)
        .where(DailyCheckin.user_id == current_user.id, DailyCheckin.date >= cutoff)
        .order_by(DailyCheckin.date.desc())
    )
    checkins = db.execute(stmt).scalars().all()
    return CheckinHistory(checkins=[CheckinRead.model_validate(c) for c in checkins], total=len(checkins))


@router.get("/{checkin_date}", response_model=CheckinRead)
def get_checkin(
    checkin_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckinRead:
    checkin = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id, DailyCheckin.date == checkin_date)
        .first()
    )
    if checkin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No check-in for this date")
    return CheckinRead.model_validate(checkin)
