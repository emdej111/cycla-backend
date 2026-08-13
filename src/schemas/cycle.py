from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CycleStart(BaseModel):
    start_date: date
    notes: str | None = None


class CycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date
    end_date: date | None
    cycle_length: int | None
    phase: str | None
    predicted_ovulation_date: date | None
    notes: str | None


class CurrentCycleRead(BaseModel):
    cycle: CycleRead
    current_day: int
    current_phase: str
    predicted_ovulation_date: date | None


class CycleHistory(BaseModel):
    cycles: list[CycleRead]
    total: int
