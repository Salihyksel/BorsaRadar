from __future__ import annotations

import os
import structlog

logger = structlog.get_logger(__name__)

_LABEL_MAP: dict[str, str] = {
    "positive": "pozitif",
    "LABEL_1": "pozitif",
    "negative": "negatif",
    "LABEL_0": "negatif",
}

_MAX_CHARS = 512

POZITIF_KELIMELER = [
    "kar", "kâr", "artış", "yükseldi", "rekor", "büyüme",
    "kazanç", "başarı", "güçlü", "olumlu", "ihracat",
    "sözleşme", "yatırım", "temettü",
]

NEGATIF_KELIMELER = [
    "zarar", "düştü", "geriledi", "kayıp", "kriz", "risk",
    "soruşturma", "ceza", "iflas", "borç", "açık",
]

def analyze_sentiment(text: str) -> str:
    """Keyword tabanlı sentiment analizi (Railway modu)."""
    if not text:
        return "nötr"
    text_lower = text.lower()
    pozitif = sum(1 for k in POZITIF_KELIMELER if k in text_lower)
    negatif = sum(1 for k in NEGATIF_KELIMELER if k in text_lower)
    if pozitif > negatif:
        return "pozitif"
    elif negatif > pozitif:
        return "negatif"
    return "nötr"
