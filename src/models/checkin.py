from datetime import date

from sqlalchemy import JSON, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.encryption import EncryptedText
from src.db.database import Base


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    cycle_id: Mapped[int | None] = mapped_column(ForeignKey("cycles.id"), nullable=True, index=True)

    # --- Physical ---
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    pain_location: Mapped[list | None] = mapped_column(JSON, nullable=True)  # e.g. ["lower_abdomen"]
    bleeding_intensity: Mapped[str | None] = mapped_column(String(20), nullable=True)  # none/light/medium/heavy
    bleeding_color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    exercise_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_intensity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    digestion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bloating: Mapped[bool | None] = mapped_column(nullable=True)
    appetite: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # --- Psychological ---
    mood: Mapped[list | None] = mapped_column(JSON, nullable=True)  # array of emotions
    anxiety_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    libido: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    social_energy: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    journal_text: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)

    # --- Skin ---
    acne: Mapped[str | None] = mapped_column(String(20), nullable=True)
    oiliness: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # --- Symptoms ---
    symptoms: Mapped[list | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="checkins")  # noqa: F821
    cycle: Mapped["Cycle | None"] = relationship("Cycle", back_populates="checkins")  # noqa: F821
