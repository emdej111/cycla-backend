from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.db.database import get_db
from src.models.checkin import DailyCheckin
from src.models.cycle import Cycle
from src.models.insight import Insight, InsightType
from src.models.user import User
from src.schemas.insight import InsightRead, PatternsResponse
from src.services.personalization import (
    build_generic_insight,
    build_personalized_insight,
    detect_patterns,
    is_personalization_eligible,
)
from src.services.phase_detector import detect_phase

router = APIRouter(prefix="/insights", tags=["insights"])


def _all_cycles(db: Session, user_id: int) -> list[Cycle]:
    stmt = select(Cycle).where(Cycle.user_id == user_id).order_by(Cycle.start_date.desc())
    return list(db.execute(stmt).scalars().all())


def _current_cycle(cycles: list[Cycle]) -> Cycle | None:
    open_cycles = [c for c in cycles if c.end_date is None]
    return open_cycles[0] if open_cycles else (cycles[0] if cycles else None)


@router.get("/today", response_model=InsightRead)
def get_today_insight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InsightRead:
    today = date.today()
    cycles = _all_cycles(db, current_user.id)
    cycle = _current_cycle(cycles)

    if cycle is None:
        phase = "follicular"
        content = build_generic_insight(phase, current_user.language)
        is_personalized = False
    else:
        phase = detect_phase(cycle.start_date, today, current_user.average_cycle_length)
        if is_personalization_eligible(current_user):
            checkins = list(
                db.execute(
                    select(DailyCheckin).where(DailyCheckin.user_id == current_user.id)
                ).scalars()
            )
            content = build_personalized_insight(current_user, cycles, checkins, phase)
            is_personalized = not content.get("personalization_unavailable", False)
        else:
            content = build_generic_insight(phase, current_user.language)
            is_personalized = False

    existing = (
        db.query(Insight)
        .filter(Insight.user_id == current_user.id, Insight.date == today, Insight.type == InsightType.DAILY)
        .first()
    )
    if existing is not None:
        existing.content = content
        existing.is_personalized = is_personalized
        insight = existing
    else:
        insight = Insight(
            user_id=current_user.id,
            date=today,
            type=InsightType.DAILY,
            content=content,
            is_personalized=is_personalized,
            scientific_sources=["ACOG Menstrual Cycle Guidelines", "Cycla static knowledge base"]
            if not is_personalized
            else [],
        )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return InsightRead.model_validate(insight)


@router.get("/weekly", response_model=InsightRead)
def get_weekly_insight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InsightRead:
    today = date.today()
    week_ago = today - timedelta(days=7)
    checkins = list(
        db.execute(
            select(DailyCheckin).where(
                DailyCheckin.user_id == current_user.id,
                DailyCheckin.date >= week_ago,
                DailyCheckin.date <= today,
            )
        ).scalars()
    )

    def _avg(values: list[float | None]) -> float | None:
        clean = [v for v in values if v is not None]
        return round(sum(clean) / len(clean), 1) if clean else None

    symptom_counts = Counter(s for c in checkins for s in (c.symptoms or []))
    mood_counts = Counter(m for c in checkins for m in (c.mood or []))

    content = {
        "days_logged": len(checkins),
        "avg_energy_level": _avg([c.energy_level for c in checkins]),
        "avg_pain_level": _avg([c.pain_level for c in checkins]),
        "avg_sleep_hours": _avg([c.sleep_hours for c in checkins]),
        "avg_stress_level": _avg([c.stress_level for c in checkins]),
        "top_symptoms": [s for s, _ in symptom_counts.most_common(5)],
        "top_moods": [m for m, _ in mood_counts.most_common(5)],
    }

    existing = (
        db.query(Insight)
        .filter(Insight.user_id == current_user.id, Insight.date == today, Insight.type == InsightType.WEEKLY)
        .first()
    )
    if existing is not None:
        existing.content = content
        insight = existing
    else:
        insight = Insight(
            user_id=current_user.id,
            date=today,
            type=InsightType.WEEKLY,
            content=content,
            is_personalized=is_personalization_eligible(current_user),
            scientific_sources=[],
        )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return InsightRead.model_validate(insight)


@router.get("/patterns", response_model=PatternsResponse)
def get_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatternsResponse:
    cycles = _all_cycles(db, current_user.id)
    checkins = list(
        db.execute(select(DailyCheckin).where(DailyCheckin.user_id == current_user.id)).scalars()
    )

    sufficient_data = is_personalization_eligible(current_user) and len(cycles) >= 2
    patterns = detect_patterns(current_user, cycles, checkins) if sufficient_data else []

    return PatternsResponse(patterns=patterns, cycles_analyzed=len(cycles), sufficient_data=sufficient_data)
