from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import CycleGoal, Language


class GynecologicalProfile(BaseModel):
    conditions: list[str] = Field(default_factory=list)  # e.g. PCOS, endometriosis, fibroids, thyroid
    contraception: str | None = None
    pregnancy_status: str | None = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    age: int | None = Field(default=None, ge=10, le=100)
    gynecological_profile: GynecologicalProfile = Field(default_factory=GynecologicalProfile)
    cycle_goal: CycleGoal = CycleGoal.HEALTH
    language: Language = Language.EN
    average_cycle_length: int = Field(default=29, ge=15, le=60)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    age: int | None
    created_at: datetime
    gynecological_profile: dict
    cycle_goal: CycleGoal
    language: Language
    average_cycle_length: int
    tracked_cycles_count: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
