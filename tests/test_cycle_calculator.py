from datetime import date, timedelta

from src.services.cycle_calculator import (
    average_cycle_length,
    calculate_cycle_length,
    current_cycle_day,
    predict_next_period,
    predict_ovulation_date,
)


def test_predict_ovulation_date_28_day_cycle():
    start = date(2026, 1, 1)
    # ovulation ~14 days before next period -> day 14 of a 28-day cycle
    assert predict_ovulation_date(start, 28) == start + timedelta(days=13)


def test_predict_ovulation_date_never_before_cycle_start():
    start = date(2026, 1, 1)
    # very short avg cycle length shouldn't push ovulation day below 1
    assert predict_ovulation_date(start, 10) == start


def test_predict_next_period():
    start = date(2026, 1, 1)
    assert predict_next_period(start, 28) == start + timedelta(days=28)


def test_calculate_cycle_length():
    start = date(2026, 1, 1)
    end = date(2026, 1, 29)
    assert calculate_cycle_length(start, end) == 28


def test_average_cycle_length_ignores_invalid_values():
    assert average_cycle_length([28, 30, 0, None, 29]) == round((28 + 30 + 29) / 3)


def test_average_cycle_length_falls_back_to_default_when_empty():
    assert average_cycle_length([], default=29) == 29


def test_current_cycle_day():
    start = date(2026, 1, 1)
    assert current_cycle_day(start, start + timedelta(days=4)) == 5
