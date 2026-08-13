"""Decides whether a user gets generic (static knowledge base) or
personalized (Claude-generated) recommendations, and detects recurring
symptom patterns across a user's cycle history.

Rule: personalization only kicks in once a user has tracked
MIN_CYCLES_FOR_PERSONALIZATION (default 3) full cycles. Below that
threshold there isn't enough history for pattern detection to be
meaningful, so we fall back to the static, evidence-based knowledge base.
"""

from collections import defaultdict
from typing import Any

from src.core.config import get_settings
from src.models.checkin import DailyCheckin
from src.models.cycle import Cycle
from src.models.user import User
from src.services import claude_service
from src.services.cycle_calculator import current_cycle_day
from src.services.knowledge_base import get_phase_knowledge
from src.services.phase_detector import detect_phase


def is_personalization_eligible(user: User) -> bool:
    settings = get_settings()
    return user.tracked_cycles_count >= settings.min_cycles_for_personalization


def build_generic_insight(phase: str, language: str = "en") -> dict[str, Any]:
    knowledge = get_phase_knowledge(phase, language)
    return {
        "phase_info": {"phase": phase, "summary": knowledge["summary"]},
        "recommendations": [rec["text"] for rec in knowledge["recommendations"]],
        "patterns_detected": [],
    }


def _serialize_checkin(checkin: DailyCheckin, cycle_day_number: int, phase: str) -> dict[str, Any]:
    return {
        "cycle_day": cycle_day_number,
        "phase": phase,
        "energy_level": checkin.energy_level,
        "pain_level": checkin.pain_level,
        "bleeding_intensity": checkin.bleeding_intensity,
        "sleep_hours": checkin.sleep_hours,
        "sleep_quality": checkin.sleep_quality,
        "mood": checkin.mood,
        "anxiety_level": checkin.anxiety_level,
        "stress_level": checkin.stress_level,
        "symptoms": checkin.symptoms,
    }


def build_personalized_insight(
    user: User,
    cycles: list[Cycle],
    checkins: list[DailyCheckin],
    current_phase: str,
) -> dict[str, Any]:
    """Assembles pattern data (no free-text journal content) and calls Claude
    for a personalized insight. Falls back to the generic insight, tagged as
    non-personalized, if the Claude call fails for any reason (e.g. API
    outage) so the user always gets a response.
    """
    checkins_by_cycle: dict[int, list[DailyCheckin]] = defaultdict(list)
    for checkin in checkins:
        if checkin.cycle_id is not None:
            checkins_by_cycle[checkin.cycle_id].append(checkin)

    cycle_history_payload = []
    for cycle in cycles:
        serialized_checkins = [
            _serialize_checkin(
                c,
                current_cycle_day(cycle.start_date, c.date),
                detect_phase(cycle.start_date, c.date, user.average_cycle_length),
            )
            for c in checkins_by_cycle.get(cycle.id, [])
        ]
        cycle_history_payload.append(
            {
                "start_date": cycle.start_date,
                "end_date": cycle.end_date,
                "cycle_length": cycle.cycle_length,
                "checkins": serialized_checkins,
            }
        )

    user_data = {
        "cycle_goal": user.cycle_goal,
        "gynecological_profile": user.gynecological_profile,
        "average_cycle_length": user.average_cycle_length,
        "tracked_cycles_count": user.tracked_cycles_count,
    }

    try:
        result = claude_service.get_personalized_insight(
            user_data=user_data,
            cycle_history=cycle_history_payload,
            current_phase=current_phase,
        )
    except Exception:
        fallback = build_generic_insight(current_phase, user.language)
        fallback["personalization_unavailable"] = True
        return fallback

    return {
        "phase_info": {"phase": current_phase, "summary": result.get("summary", "")},
        "recommendations": result.get("recommendations", []),
        "patterns_detected": result.get("patterns_detected", []),
    }


def detect_patterns(
    user: User,
    cycles: list[Cycle],
    checkins: list[DailyCheckin],
    min_occurrences: int = 2,
    day_window: int = 1,
) -> list[dict[str, Any]]:
    """Finds symptoms that recur on similar cycle days across multiple
    cycles. `day_window` buckets nearby days together (e.g. day 13-15
    treated as "around day 14") since cycles rarely align perfectly.
    """
    cycles_by_id = {cycle.id: cycle for cycle in cycles}

    # symptom -> list of (cycle_id, cycle_day)
    occurrences: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for checkin in checkins:
        cycle = cycles_by_id.get(checkin.cycle_id)
        if cycle is None:
            continue
        day = current_cycle_day(cycle.start_date, checkin.date)
        for symptom in checkin.symptoms or []:
            occurrences[symptom].append((cycle.id, day))

    patterns: list[dict[str, Any]] = []
    for symptom, entries in occurrences.items():
        # bucket by day rounded to the nearest window
        buckets: dict[int, set[int]] = defaultdict(set)
        for cycle_id, day in entries:
            bucket_key = round(day / (day_window * 2 + 1))
            buckets[bucket_key].add(cycle_id)

        best_bucket, best_cycles = max(buckets.items(), key=lambda kv: len(kv[1]), default=(None, set()))
        if best_bucket is None or len(best_cycles) < min_occurrences:
            continue

        typical_days = sorted({day for cid, day in entries if round(day / (day_window * 2 + 1)) == best_bucket})
        representative_day = typical_days[len(typical_days) // 2]
        representative_cycle = cycles_by_id[next(iter(best_cycles))]
        typical_phase = detect_phase(
            representative_cycle.start_date,
            representative_cycle.start_date.fromordinal(
                representative_cycle.start_date.toordinal() + representative_day - 1
            ),
            user.average_cycle_length,
        )

        patterns.append(
            {
                "symptom": symptom,
                "typical_cycle_days": typical_days,
                "typical_phase": typical_phase,
                "occurrences": len(best_cycles),
                "confidence": round(len(best_cycles) / max(len(cycles), 1), 2),
            }
        )

    patterns.sort(key=lambda p: p["occurrences"], reverse=True)
    return patterns
