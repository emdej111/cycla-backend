from datetime import date

from pydantic import BaseModel, ConfigDict

from src.models.insight import InsightType


class InsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    type: InsightType
    content: dict
    is_personalized: bool
    scientific_sources: list[str] | None


class PatternDetected(BaseModel):
    symptom: str
    typical_cycle_days: list[int]
    typical_phase: str
    occurrences: int
    confidence: float


class PatternsResponse(BaseModel):
    patterns: list[PatternDetected]
    cycles_analyzed: int
    sufficient_data: bool
