from datetime import date, timedelta
from types import SimpleNamespace

from src.services.knowledge_base import get_phase_knowledge
from src.services.personalization import build_generic_insight, detect_patterns, is_personalization_eligible


def _user(tracked_cycles_count=0, average_cycle_length=28, language="en"):
    return SimpleNamespace(
        tracked_cycles_count=tracked_cycles_count,
        average_cycle_length=average_cycle_length,
        language=language,
    )


def test_personalization_requires_3_cycles():
    assert is_personalization_eligible(_user(tracked_cycles_count=2)) is False
    assert is_personalization_eligible(_user(tracked_cycles_count=3)) is True
    assert is_personalization_eligible(_user(tracked_cycles_count=5)) is True


def test_build_generic_insight_returns_static_knowledge():
    insight = build_generic_insight("luteal", "en")
    assert insight["phase_info"]["phase"] == "luteal"
    assert len(insight["recommendations"]) > 0
    assert insight["patterns_detected"] == []


def test_generic_insight_supports_croatian():
    en = get_phase_knowledge("menstrual", "en")
    hr = get_phase_knowledge("menstrual", "hr")
    assert en["summary"] != hr["summary"]
    assert len(hr["recommendations"]) == len(en["recommendations"])


def test_detect_patterns_finds_recurring_symptom_on_same_cycle_day():
    cycles = [
        SimpleNamespace(id=1, start_date=date(2026, 1, 1)),
        SimpleNamespace(id=2, start_date=date(2026, 1, 29)),
        SimpleNamespace(id=3, start_date=date(2026, 2, 26)),
    ]
    checkins = [
        SimpleNamespace(cycle_id=1, date=date(2026, 1, 3), symptoms=["cramps"]),
        SimpleNamespace(cycle_id=2, date=date(2026, 1, 31), symptoms=["cramps"]),
        SimpleNamespace(cycle_id=3, date=date(2026, 2, 28), symptoms=["cramps"]),
        SimpleNamespace(cycle_id=1, date=date(2026, 1, 20), symptoms=["bloating"]),
    ]
    user = _user(tracked_cycles_count=3)

    patterns = detect_patterns(user, cycles, checkins, min_occurrences=2)

    cramps_pattern = next(p for p in patterns if p["symptom"] == "cramps")
    assert cramps_pattern["occurrences"] == 3
    assert cramps_pattern["typical_phase"] == "menstrual"
    assert all(p["symptom"] != "bloating" for p in patterns)  # only 1 occurrence, below threshold


def test_detect_patterns_returns_empty_for_no_checkins():
    user = _user(tracked_cycles_count=3)
    assert detect_patterns(user, [], []) == []
