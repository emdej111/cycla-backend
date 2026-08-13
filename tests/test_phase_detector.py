from datetime import date, timedelta

from src.services.phase_detector import cycle_day, detect_phase


def test_menstrual_phase_days_1_to_5():
    start = date(2026, 1, 1)
    for offset in range(0, 5):
        assert detect_phase(start, start + timedelta(days=offset), 28) == "menstrual"


def test_follicular_phase():
    start = date(2026, 1, 1)
    # day 10 of a 28-day cycle: 10 <= 28*0.45 (12.6) -> follicular
    assert detect_phase(start, start + timedelta(days=9), 28) == "follicular"


def test_ovulatory_phase():
    start = date(2026, 1, 1)
    # day 14 of a 28-day cycle: 12.6 < 14 <= 15.4 -> ovulatory
    assert detect_phase(start, start + timedelta(days=13), 28) == "ovulatory"


def test_luteal_phase():
    start = date(2026, 1, 1)
    # day 20 of a 28-day cycle: > 15.4 -> luteal
    assert detect_phase(start, start + timedelta(days=19), 28) == "luteal"


def test_phase_boundaries_scale_with_avg_cycle_length():
    start = date(2026, 1, 1)
    # 35-day cycle: follicular boundary at 35*0.45 = 15.75
    assert detect_phase(start, start + timedelta(days=14), 35) == "follicular"
    assert detect_phase(start, start + timedelta(days=15), 35) == "follicular"


def test_cycle_day_is_1_indexed_and_never_below_1():
    start = date(2026, 1, 1)
    assert cycle_day(start, start) == 1
    assert cycle_day(start, start + timedelta(days=5)) == 6
    # a date before the recorded start (clock skew / bad input) should not
    # produce a non-positive day
    assert cycle_day(start, start - timedelta(days=10)) == 1
