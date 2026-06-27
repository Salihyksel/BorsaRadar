from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

POZITIF_KELIMELER = [
    "kar", "kâr", "artış", "yükseldi", "rekor", "büyüme",
    "kazanç", "başarı", "güçlü", "olumlu", "ihracat",
    "sözleşme", "yatırım", "temettü",
]

NEGATIF_KELIMELER = [
    "zarar", "düştü", "geriledi", "kayıp", "kriz", "risk",
    "soruşturma", "ceza", "iflas", "borç", "açık",
]

def analyze_sentiment(text: str) -> dict:
    """Keyword tabanlı sentiment analizi. Dict döndürür."""
    if not text:
        return {"sentiment": "nötr", "skor": 0.0}
    text_lower = text.lower()
    pozitif = sum(1 for k in POZITIF_KELIMELER if k in text_lower)
    negatif = sum(1 for k in NEGATIF_KELIMELER if k in text_lower)
    if pozitif > negatif:
        return {"sentiment": "pozitif", "skor": round(pozitif / (pozitif + negatif), 2)}
    elif negatif > pozitif:
        return {"sentiment": "negatif", "skor": round(negatif / (pozitif + negatif), 2)}
    return {"sentiment": "nötr", "skor": 0.5}
