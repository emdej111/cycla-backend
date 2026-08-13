# Cycla — Project Documentation

> A menstrual cycle tracking app with AI personalization, built with FastAPI + PostgreSQL backend and React Native frontend.

---

## App concept

Cycla is a cycle tracking app that starts with evidence-based population averages and becomes increasingly personalized as the user logs more data. Unlike existing apps (Clue, Flo, Natural Cycles) that assume a 28-day cycle and deliver generic advice, Cycla learns each user's individual pattern and delivers context-aware, scientifically grounded recommendations.

**Key differentiator:** Cycla does not prescribe rigid phase-locked protocols. Instead, it uses symptom-directed personalization — detecting the user's real patterns after 3+ tracked cycles and adapting recommendations accordingly.

---

## Scientific foundation

Based on peer-reviewed research from PubMed and npj Digital Medicine. Key sources:

- Bull et al., 2019 (*npj Digital Medicine*, 612,613 cycles) — real-world cycle length variation
- McNulty et al., 2020 (*Sports Medicine*) — exercise performance across cycle phases
- Thys-Jacobs et al., 1998 (*AJOG*) — calcium and PMS (landmark RCT, n=466)
- Snipe et al., 2024 (*Nutrition & Dietetics*) — omega-3 and dysmenorrhea
- Apple Women's Health Study, 2023 (*npj Digital Medicine*, 165,668 cycles)

**Important caveat:** "Cycle syncing" is popular but weakly supported by evidence. Cycla frames phase awareness as symptom management, not rigid phase-locked protocols.

---

## Personalization logic

### Stage 1 — Cycles 1–3 (generic)
- App uses population averages (mean cycle 29.3 days, follicular phase ~16.9 days, luteal ~12.4 days)
- Delivers evidence-based general recommendations per phase
- Collects: period dates, cycle length, daily symptoms

### Stage 2 — Cycles 4–6 (light personalization)
- App detects user's real follicular/luteal lengths
- Identifies recurring symptom patterns (e.g. headache always 3 days before menses)
- Delivers symptom-targeted interventions: calcium, magnesium, omega-3, ginger

### Stage 3 — Cycles 6+ (full personalization)
- Claude API receives user's full cycle history and symptom patterns
- Generates individualized daily recommendations
- Flags irregularities for medical review

```python
if user.tracked_cycles < 3:
    return generic_recommendations(predicted_phase)
else:
    return claude_personalized(user.cycle_history, user.symptoms)
```

---

## The four phases — evidence-based summary

### Menstrual (days 1–5)
- Hormones: estrogen + progesterone at lowest
- Physical: potential fatigue, cramping, lower pain threshold
- Nutrition: iron-rich foods (heme sources + vitamin C), anti-inflammatory (ginger, omega-3)
- Exercise: gentle movement, yoga, walking — no physiological reason to stop training
- Sleep: most disrupted phase — prioritize rest
- Evidence strength: strong for hormonal profile; moderate for symptom clustering

### Follicular (day 1 to ovulation, ~16.9 days average)
- Hormones: estrogen rising, FSH active
- Physical: energy increasing, mood improving
- Nutrition: adequate protein, complex carbs, variety
- Exercise: good window for higher intensity — estrogen supports performance
- Evidence strength: moderate (follicular length is highly variable — 10–30 days)

### Ovulatory (~24–36h around LH surge)
- Hormones: LH peaks, estrogen peaks, small testosterone rise
- Physical: peak energy, libido may increase
- Nutrition: anti-inflammatory foods, adequate hydration
- Exercise: peak performance window — note higher knee laxity (ACL risk)
- Evidence strength: strong for hormonal events; weak for performance claims

### Luteal (ovulation to menses, ~12.4 days average)
- Hormones: progesterone peaks, then both fall
- Physical: higher core temp (+0.3–0.5°C), higher perceived exertion, potential PMS
- Nutrition: calcium 1200mg/day, magnesium 200–300mg, omega-3, reduce caffeine
- Exercise: autoregulate by feel — heat management important
- Sleep: most disrupted luteal → cooler sleep environment
- Evidence strength: strong for temperature; moderate for nutrition interventions

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.12 |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| Auth | JWT (python-jose + passlib) |
| Frontend | React Native + Expo |
| PDF processing | pdfplumber |

---

## Backend architecture

```
cycla-backend/
├── src/
│   ├── api/routes/        # auth, cycles, checkins, insights, chat, documents
│   ├── models/            # SQLAlchemy models
│   ├── services/          # business logic + Claude integration
│   ├── db/                # database connection + migrations
│   └── core/              # config + security
├── tests/
├── CLAUDE.md
├── requirements.txt
└── .env.example
```

### Key API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | User registration with gynecological profile |
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

## User data collected

### Onboarding
- Name, age, last period date, average cycle length
- Gynecological conditions: PCOS, endometriosis, fibroids, thyroid issues
- Contraception status, pregnancy/breastfeeding/perimenopause
- App goal: health / sport / fertility / symptom management / psychological support
- Language: Croatian / English

### Daily check-in

**Physical:**
energy, pain level + location, bleeding (intensity + color), sleep hours + quality, weight, exercise type + intensity, digestion, bloating, appetite, skin (acne, oiliness)

**Psychological:**
mood (multi-select emotions), anxiety 1–10, libido 1–5, stress 1–10, social energy 1–10, free journal text

**Symptoms:**
headache, cramps, breast tenderness, nausea, fatigue, bloating, back pain, mood swings

---

## Medical document analysis

Users can upload:
- Blood test results (hormones, iron, ferritin)
- Ultrasound reports
- Gynecological examination results

Claude analyzes and:
- Explains results in plain language
- Flags values outside normal range
- Stores in profile and uses to personalize recommendations
- Always appends: *"This is not medical advice. Consult your healthcare provider."*

---

## Safety & compliance

- JWT authentication on all endpoints
- Health data encrypted at rest
- GDPR compliant: data export + account deletion
- Medical disclaimer on all AI responses
- Red flags auto-detected: cycles <21 or >35 days, severe premenstrual mood symptoms, heavy bleeding
- App never diagnoses — always recommends consulting a healthcare provider

---

## Disclaimer

Cycla is a wellness tracking tool, not a medical device. Recommendations are based on population-level research and should not replace professional medical advice. Individual responses to cycle phases vary significantly — what works for the average may not work for you.

---

*Built with Claude Code + Lovable | Scientific foundation: PubMed peer-reviewed research*
*Last updated: August 2026*
