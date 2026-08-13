"""Loader for the static, evidence-informed phase knowledge base used for
generic (non-personalized) recommendations, i.e. before a user has 3+
tracked cycles. See src/services/data/knowledge_base.json.
"""

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "knowledge_base.json"


@lru_cache
def load_knowledge_base() -> dict:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_phase_knowledge(phase: str, language: str = "en") -> dict:
    kb = load_knowledge_base()
    phase_data = kb.get(phase, {})
    if not phase_data:
        return {"summary": "", "recommendations": []}

    summary = phase_data.get("summary", {}).get(language) or phase_data.get("summary", {}).get("en", "")
    recommendations = [
        {
            "category": rec.get("category"),
            "text": rec.get(language) or rec.get("en"),
        }
        for rec in phase_data.get("recommendations", [])
    ]
    return {"summary": summary, "recommendations": recommendations}
