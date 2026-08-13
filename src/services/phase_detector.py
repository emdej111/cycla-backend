"""Cycle phase detection.

Phase boundaries are expressed as a fraction of the user's average cycle
length (rather than fixed day counts) so the model adapts to cycles shorter
or longer than the textbook 28 days. Menstrual phase is capped at day 5
regardless of cycle length, matching typical bleeding duration.
"""

from datetime import date

PHASES = ("menstrual", "follicular", "ovulatory", "luteal")


def detect_phase(cycle_start: date, current_date: date, avg_cycle_length: int) -> str:
    day = (current_date - cycle_start).days + 1
    if day <= 5:
        return "menstrual"
    elif day <= avg_cycle_length * 0.45:
        return "follicular"
    elif day <= avg_cycle_length * 0.55:
        return "ovulatory"
    else:
        return "luteal"


def cycle_day(cycle_start: date, current_date: date) -> int:
    """1-indexed day of the cycle. Never returns less than 1."""
    return max((current_date - cycle_start).days + 1, 1)
