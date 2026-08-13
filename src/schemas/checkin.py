from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CheckinCreate(BaseModel):
    date: date

    # Physical
    energy_level: int | None = Field(default=None, ge=1, le=10)
    pain_level: int | None = Field(default=None, ge=1, le=10)
    pain_location: list[str] | None = None
    bleeding_intensity: str | None = None  # none/light/medium/heavy
    bleeding_color: str | None = None
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: int | None = Field(default=None, ge=1, le=10)
    weight_kg: float | None = Field(default=None, gt=0, le=400)
    exercise_type: str | None = None
    exercise_intensity: str | None = None
    digestion: str | None = None
    bloating: bool | None = None
    appetite: str | None = None

    # Psychological
    mood: list[str] | None = None
    anxiety_level: int | None = Field(default=None, ge=1, le=10)
    libido: int | None = Field(default=None, ge=1, le=5)
    stress_level: int | None = Field(default=None, ge=1, le=10)
    social_energy: int | None = Field(default=None, ge=1, le=10)
    journal_text: str | None = None

    # Skin
    acne: str | None = None
    oiliness: str | None = None

    # Symptoms
    symptoms: list[str] | None = None


class CheckinRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    cycle_id: int | None

    energy_level: int | None
    pain_level: int | None
    pain_location: list[str] | None
    bleeding_intensity: str | None
    bleeding_color: str | None
    sleep_hours: float | None
    sleep_quality: int | None
    weight_kg: float | None
    exercise_type: str | None
    exercise_intensity: str | None
    digestion: str | None
    bloating: bool | None
    appetite: str | None

    mood: list[str] | None
    anxiety_level: int | None
    libido: int | None
    stress_level: int | None
    social_energy: int | None
    journal_text: str | None

    acne: str | None
    oiliness: str | None

    symptoms: list[str] | None


class CheckinHistory(BaseModel):
    checkins: list[CheckinRead]
    total: int
