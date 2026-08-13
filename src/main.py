import logging

from fastapi import FastAPI

from src.api.middleware import register_middleware
from src.api.routes import auth, chat, checkins, cycles, documents, insights, user
from src.core.config import get_settings
from src.db.database import Base, engine

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Menstrual cycle tracking API with AI-driven personalization.",
    version="0.1.0",
)

register_middleware(app)

app.include_router(auth.router)
app.include_router(cycles.router)
app.include_router(checkins.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(user.router)


@app.on_event("startup")
def on_startup() -> None:
    # Creates tables if they don't exist yet. In production, schema changes
    # should go through Alembic migrations (see src/db/migrations) instead.
    import src.models  # noqa: F401  (registers all models with Base.metadata)

    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
