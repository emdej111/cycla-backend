from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.cycle import Cycle
from src.models.user import User
from src.schemas.cycle import CurrentCycleRead, CycleHistory, CycleRead, CycleStart
from src.services.cycle_calculator import (
    average_cycle_length,
    calculate_cycle_length,
    current_cycle_day,
    predict_ovulation_date,
)
from src.services.phase_detector import detect_phase

router = APIRouter(prefix="/cycles", tags=["cycles"])


def _latest_open_cycle(db: Session, user_id: int) -> Cycle | None:
    stmt = (
        select(Cycle)
        .where(Cycle.user_id == user_id, Cycle.end_date.is_(None))
        .order_by(Cycle.start_date.desc())
    )
    return db.execute(stmt).scalars().first()


@router.post("/start", response_model=CycleRead, status_code=status.HTTP_201_CREATED)
def start_cycle(
    payload: CycleStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CycleRead:
    previous_open = _latest_open_cycle(db, current_user.id)
    if previous_open is not None:
        if payload.start_date <= previous_open.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New cycle start_date must be after the current cycle's start_date",
            )
        previous_open.end_date = payload.start_date
        previous_open.cycle_length = calculate_cycle_length(previous_open.start_date, payload.start_date)
        db.add(previous_open)

        current_user.tracked_cycles_count += 1
        past_lengths = [
            c.cycle_length
            for c in db.execute(
                select(Cycle).where(Cycle.user_id == current_user.id, Cycle.cycle_length.is_not(None))
            )
            .scalars()
            .all()
        ]
        current_user.average_cycle_length = average_cycle_length(
            past_lengths, default=current_user.average_cycle_length
        )
        db.add(current_user)

    new_cycle = Cycle(
        user_id=current_user.id,
        start_date=payload.start_date,
        phase="menstrual",
        predicted_ovulation_date=predict_ovulation_date(payload.start_date, current_user.average_cycle_length),
        notes=payload.notes,
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    return CycleRead.model_validate(new_cycle)


@router.get("/current", response_model=CurrentCycleRead)
def get_current_cycle(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurrentCycleRead:
    cycle = _latest_open_cycle(db, current_user.id)
    if cycle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active cycle. Start one first.")

    today = date.today()
    phase = detect_phase(cycle.start_date, today, current_user.average_cycle_length)
    if phase != cycle.phase:
        cycle.phase = phase
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

    return CurrentCycleRead(
        cycle=CycleRead.model_validate(cycle),
        current_day=current_cycle_day(cycle.start_date, today),
        current_phase=phase,
        predicted_ovulation_date=cycle.predicted_ovulation_date,
    )


@router.get("/history", response_model=CycleHistory)
def get_cycle_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CycleHistory:
    stmt = select(Cycle).where(Cycle.user_id == current_user.id).order_by(Cycle.start_date.desc())
    cycles = db.execute(stmt).scalars().all()
    return CycleHistory(cycles=[CycleRead.model_validate(c) for c in cycles], total=len(cycles))
