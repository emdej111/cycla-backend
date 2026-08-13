import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class CycleGoal(str, enum.Enum):
    HEALTH = "health"
    SPORT = "sport"
    FERTILITY = "fertility"
    SYMPTOM_MANAGEMENT = "symptom_management"
    PSYCHOLOGICAL_SUPPORT = "psychological_support"


class Language(str, enum.Enum):
    HR = "hr"
    EN = "en"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # conditions (PCOS, endometriosis, fibroids, thyroid), contraception, pregnancy_status
    gynecological_profile: Mapped[dict] = mapped_column(JSON, default=dict)

    cycle_goal: Mapped[CycleGoal] = mapped_column(
        Enum(CycleGoal, native_enum=False), default=CycleGoal.HEALTH, nullable=False
    )
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False), default=Language.EN, nullable=False
    )

    average_cycle_length: Mapped[int] = mapped_column(Integer, default=29, nullable=False)
    tracked_cycles_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    cycles: Mapped[list["Cycle"]] = relationship(
        "Cycle", back_populates="user", cascade="all, delete-orphan"
    )
    checkins: Mapped[list["DailyCheckin"]] = relationship(
        "DailyCheckin", back_populates="user", cascade="all, delete-orphan"
    )
    insights: Mapped[list["Insight"]] = relationship(
        "Insight", back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["MedicalDocument"]] = relationship(
        "MedicalDocument", back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="user", cascade="all, delete-orphan"
    )
