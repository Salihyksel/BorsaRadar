from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

POZITIF_KELIMELER = [
    # Türkçe
    "kar", "kâr", "artış", "arttı", "yükseldi", "yükseliş", "rekor",
    "büyüme", "büyüdü", "kazanç", "kazandı", "başarı", "başarılı",
    "güçlü", "güçlendi", "olumlu", "ihracat", "sözleşme", "yatırım",
    "temettü", "genişledi", "genişleme", "iyileşti", "iyileşme",
    "onay", "onaylandı", "destek", "teşvik", "canlandı", "toparlandı",
    "yüzde kazandı", "değer kazandı", "prim yaptı", "ralli",
    "zirve", "tavan", "yükselişte", "kazanımlar", "beklentilerin üzerinde",
    "kâr açıkladı", "gelir artışı", "verimlilik", "ihale kazandı",
    "anlaşma sağlandı", "ortaklık kurdu", "genişletiyor",
    # İngilizce
    "surge", "soar", "rally", "gain", "gains", "rise", "rises", "rose",
    "jump", "jumps", "boost", "boosts", "record high", "outperform",
    "beat expectations", "profit", "profits", "growth", "grew",
    "strong", "upgrade", "upgraded", "expansion", "recovery", "rebound",
    "bullish", "positive", "success", "successful", "top pick",
]

NEGATIF_KELIMELER = [
    # Türkçe
    "zarar", "düştü", "düşüş", "geriledi", "gerileme", "kayıp",
    "kriz", "risk", "riskli", "soruşturma", "ceza", "cezalandırıldı",
    "iflas", "borç", "açık", "daraldı", "daralma", "çöktü", "çöküş",
    "tepki", "protesto", "grev", "kesinti", "azaldı", "azalış",
    "değer kaybetti", "sert düşüş", "dip", "taban", "durgunluk",
    "olumsuz", "endişe", "belirsizlik", "gerginlik", "kesildi",
    "iptal", "iptal edildi", "gerileme kaydetti", "sıkıntı",
    "yaptırım", "dava açıldı", "el koyma", "haciz", "tasfiye",
    "işten çıkarma", "istifa", "kovuldu", "skandal",
    # İngilizce
    "plunge", "plunges", "crash", "crashes", "slump", "tumble",
    "decline", "declines", "fall", "falls", "fell", "drop", "drops",
    "loss", "losses", "downgrade", "downgraded", "weak", "warning",
    "layoffs", "bankruptcy", "lawsuit", "fraud", "investigation",
    "recession", "bearish", "negative", "concern", "concerns",
    "sell-off", "selloff", "underperform", "miss expectations",
    "cut", "cuts", "slashed", "worst",
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
