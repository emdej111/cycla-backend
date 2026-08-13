# Cycla Backend — CLAUDE.md

## Project description

Cycla is a menstrual cycle tracking app with AI personalization. This is the FastAPI Python backend that handles authentication, cycle tracking, daily check-ins, AI-powered insights, and medical document analysis.

## Architecture

- **Framework:** FastAPI + Python 3.12
- **Database:** PostgreSQL + SQLAlchemy + Alembic migrations
- **AI:** Anthropic Claude API (claude-sonnet-4-6)
- **Auth:** JWT (python-jose + passlib bcrypt)
- **PDF processing:** pdfplumber

## Project structure

```
src/
├── api/routes/     # HTTP endpoints — one file per resource
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic — keep routes thin
├── db/             # Database connection and session
└── core/           # Config, security, JWT utilities
```

## Coding conventions

- All new routes go in `src/api/routes/` — one file per resource
- Routes must be thin — business logic belongs in `src/services/`
- Use Pydantic schemas for all request/response validation
- All database operations use SQLAlchemy sessions via dependency injection
- Type hints on all function signatures — no bare `Any`
- All comments and docstrings in English

## Personalization logic

```python
if user.tracked_cycles < 3:
    # Use static knowledge base — population averages
    return generic_recommendations(predicted_phase)
else:
    # Use Claude API with user's personal pattern data
    return claude_personalized(user.cycle_history, user.symptoms)
```

Never deliver strong phase-specific prescriptions until at least 3 cycles are tracked.

## Hard rules — enforced, not optional

- **Never give medical diagnoses** — Cycla is a wellness tool, not a medical device
- **Always append disclaimer** to every AI response: *"This is not medical advice. Consult your healthcare provider."*
- **Never store API keys in code** — use environment variables only
- **Never commit .env files** — .env is in .gitignore
- **Never expose password hashes** in API responses
- **GDPR compliance** — always support data export (GET /user/export) and deletion (DELETE /user)

## Environment variables

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — long random string for JWT signing
- `ANTHROPIC_API_KEY` — from console.anthropic.com

## Running locally

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

## Running tests

```bash
pytest tests/ -v
```
