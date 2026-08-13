# Cycla Backend 🌸

> FastAPI backend for Cycla — a menstrual cycle tracking app with AI personalization powered by Claude.

---

## What is Cycla?

Cycla tracks menstrual cycles and delivers evidence-based, personalized health recommendations. Unlike existing apps that assume a 28-day cycle and deliver generic advice, Cycla learns each user's individual pattern and adapts recommendations after 3+ tracked cycles.

**Key features:**
- Cycle and phase tracking with scientific phase detection
- Daily holistic check-in (physical + psychological)
- AI-powered insights (generic → personalized after 3 cycles)
- Medical document analysis via Claude API
- Conversational AI chat with cycle context
- GDPR compliant — full data export and deletion

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Python 3.12 |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| Auth | JWT (python-jose + passlib) |
| PDF | pdfplumber |

---

## Getting started

```bash
# Clone and set up environment
git clone https://github.com/emdej111/cycla-backend.git
cd cycla-backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and DATABASE_URL

# Run
uvicorn src.main:app --reload
```

API docs: **http://localhost:8000/docs**

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register with gynecological profile |
| POST | /auth/login | JWT login |
| POST | /cycles/start | Start new cycle |
| GET | /cycles/current | Current cycle + predicted phase |
| POST | /checkins/ | Daily holistic check-in |
| GET | /insights/today | Daily insight (generic or personalized) |
| GET | /insights/patterns | Detected symptom patterns |
| POST | /chat/ | Chat with Cycla AI |
| POST | /documents/upload | Upload medical document for AI analysis |
| GET | /user/export | GDPR data export |
| DELETE | /user | GDPR account deletion |

---

## Personalization logic

```
Cycles 1–3:   Generic recommendations (population averages)
Cycles 4–6:   Light personalization (symptom patterns detected)  
Cycles 6+:    Full AI personalization via Claude API
```

---

## Running tests

```bash
pytest tests/ -v
```

---

## Important disclaimer

Cycla is a wellness tracking tool, not a medical device. All AI responses include the disclaimer: *"This is not medical advice. Consult your healthcare provider."*

---

*Built with Claude Code | Scientific foundation: PubMed peer-reviewed research*
*Last updated: August 2026*
