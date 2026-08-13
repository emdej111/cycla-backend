"""Cycle-level calculations: ovulation prediction, cycle length stats,
and next-period estimation. Builds on phase_detector.detect_phase for
per-day phase classification.
"""

from datetime import date, timedelta

from src.services.phase_detector import cycle_day, detect_phase

__all__ = [
    "predict_ovulation_date",
    "predict_next_period",
    "current_phase_for_cycle",
    "calculate_cycle_length",
    "average_cycle_length",
]


def predict_ovulation_date(cycle_start: date, avg_cycle_length: int) -> date:
    """Ovulation is estimated at ~14 days before the next expected period,
    which for a cycle of length L falls on day (L - 14) of the current cycle.
    """
    ovulation_day = max(avg_cycle_length - 14, 1)
    return cycle_start + timedelta(days=ovulation_day - 1)


def predict_next_period(cycle_start: date, avg_cycle_length: int) -> date:
    return cycle_start + timedelta(days=avg_cycle_length)


def current_phase_for_cycle(cycle_start: date, current_date: date, avg_cycle_length: int) -> str:
    return detect_phase(cycle_start, current_date, avg_cycle_length)


def calculate_cycle_length(start_date: date, end_date: date) -> int:
    """Length of a completed cycle: days from this cycle's start up to (but
    not including) the next cycle's start, i.e. end_date is the next cycle's
    start_date.
    """
    return (end_date - start_date).days


def average_cycle_length(cycle_lengths: list[int], default: int = 29) -> int:
    valid = [length for length in cycle_lengths if length and length > 0]
    if not valid:
        return default
    return round(sum(valid) / len(valid))


def current_cycle_day(cycle_start: date, current_date: date) -> int:
    return cycle_day(cycle_start, current_date)
