import enum
from datetime import date

from sqlalchemy import JSON, Boolean, Date, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class InsightType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    PATTERN = "pattern"


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[InsightType] = mapped_column(Enum(InsightType, native_enum=False), nullable=False)

    # phase_info, recommendations, patterns_detected
    content: Mapped[dict] = mapped_column(JSON, default=dict)

    is_personalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scientific_sources: Mapped[list | None] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship("User", back_populates="insights")  # noqa: F821
